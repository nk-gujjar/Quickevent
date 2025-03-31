# Description: Streamlit app for scheduling events using Google Calendar and LLM API

import streamlit as st
import json
import logging
from datetime import datetime, timedelta
import pytz
import os
from calendar_utils import get_calendar_service, create_calendar_event, list_upcoming_events
from llm_utils import query_groq, extract_json_from_text


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Now attempt to import the required modules
try:
    from calendar_utils import get_calendar_service, create_calendar_event, list_upcoming_events
    from llm_utils import query_groq, extract_json_from_text
    from datetime import datetime, timedelta
    import pytz
except ImportError as e:
    st.error(f"Failed to import required modules: {str(e)}")
    st.error("Please make sure all dependencies are installed. You may need to restart the app.")
    logger.error(f"Import error: {str(e)}")
    st.stop()

def main():
    st.title('Calendar Event Scheduler')
    st.subheader('Chat with me to schedule your events')
    
    # Initialize Google Calendar service
    try:
        calendar_service = get_calendar_service()
        st.sidebar.success("✅ Connected to Google Calendar")
    except Exception as e:
        st.sidebar.error(f"Failed to connect to Google Calendar: {str(e)}")
        st.error("Authentication failed. Please check your Google Calendar credentials.")
        st.info("If you're running this locally, make sure to set up the required secrets or environment variables.")
        st.stop()
    
    # Initialize chat history in session state if it doesn't exist
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    
    # Display chat history
    for message in st.session_state['messages']:
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            st.write(content)
    
    # Get user input
    user_prompt = st.chat_input("Tell me about the event you want to schedule...")
    
    if user_prompt:
        # Add user message to chat history
        st.session_state['messages'].append({"role": "user", "content": user_prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_prompt)
        
        # Get current date and time information for context
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        current_timezone = datetime.now(pytz.timezone('UTC')).astimezone().tzinfo
        
        # Prepare messages for API call with date context
        api_messages = [
            {"role": "system", "content": f"""You are a helpful calendar assistant. Today's date is {current_date} and the current time is {current_time} in timezone {current_timezone}.

Extract event details from the user's input and provide them in a valid JSON format that matches Google Calendar's event format. Include the following fields when possible:
- summary: Event title
- location: Event location
- description: Event description
- start: Object with dateTime (in ISO format with timezone, e.g. "2025-03-15T09:00:00+05:30") and timeZone
- end: Object with dateTime and timeZone 
- colorId: A number from 1-11 representing the event color
- attendees: Array of objects with email addresses
- recurrence: Array of RRULE strings if the event repeats

When user mentions relative dates like "today", "tomorrow", "next week", etc., convert them to actual dates based on the current date provided above.

Only include fields that are specifically mentioned by the user. Format dates correctly in ISO format with timezone.
If you cannot determine the date or time information from the user's input, include an "error" field with value "incomplete_time_info" in your JSON response.

Respond only with the JSON object and no additional text."""},
            {"role": "user", "content": user_prompt}
        ]
        
        # Show a spinner while waiting for the response
        with st.spinner("Processing your request..."):
            response = query_groq(api_messages)
        
        if "error" in response:
            st.error(f"Error: {response['error']}")
            st.text("Debug Details:")
            st.text(response.get("details", "No additional details available."))
        else:
            # Extract the JSON content from the response
            assistant_content = response['choices'][0]['message']['content']
            
            try:
                # Parse the JSON response
                event_json = json.loads(assistant_content)
                
                # Debug info in sidebar
                with st.sidebar.expander("Debug - LLM Response"):
                    st.json(event_json)
                
                # Check if the LLM indicated incomplete time information
                if event_json.get("error") == "incomplete_time_info":
                    assistant_response = "❌ Not able to get the time or details are incomplete. Please provide more specific date and time information."
                    st.session_state['messages'].append({"role": "assistant", "content": assistant_response})
                    with st.chat_message("assistant"):
                        st.write(assistant_response)
                    return
                
                # Check if start time is missing
                if not event_json.get('start', {}).get('dateTime'):
                    assistant_response = "❌ Not able to get the time or details are incomplete. Please provide more specific date and time information."
                    st.session_state['messages'].append({"role": "assistant", "content": assistant_response})
                    with st.chat_message("assistant"):
                        st.write(assistant_response)
                    return
                
                # Create the event in Google Calendar
                result = create_calendar_event(calendar_service, event_json)
                
                # Prepare the response to show the user
                if result.get("success"):
                    event_details = f"""
                    ✅ Event created successfully!
                    
                    📌 Title: {event_json.get('summary')}
                    🕒 When: {event_json.get('start', {}).get('dateTime')} to {event_json.get('end', {}).get('dateTime')}
                    📍 Where: {event_json.get('location', 'No location specified')}
                    📝 Description: {event_json.get('description', 'No description')}
                    🔗 Calendar Link: {result.get('link')}
                    """
                    
                    if 'attendees' in event_json:
                        attendees_list = ", ".join([attendee.get('email') for attendee in event_json.get('attendees', [])])
                        event_details += f"\n👥 Attendees: {attendees_list}"
                    
                    assistant_response = event_details
                else:
                    assistant_response = f"❌ Failed to create event: {result.get('error')}"
                    
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the text
                extracted_json = extract_json_from_text(assistant_content)
                
                if extracted_json:
                    # Debug info in sidebar
                    with st.sidebar.expander("Debug - Extracted JSON"):
                        st.json(extracted_json)
                    
                    # Check if the LLM indicated incomplete time information
                    if extracted_json.get("error") == "incomplete_time_info":
                        assistant_response = "❌ Not able to get the time or details are incomplete. Please provide more specific date and time information."
                        st.session_state['messages'].append({"role": "assistant", "content": assistant_response})
                        with st.chat_message("assistant"):
                            st.write(assistant_response)
                        return
                    
                    # Check if start time is missing
                    if not extracted_json.get('start', {}).get('dateTime'):
                        assistant_response = "❌ Not able to get the time or details are incomplete. Please provide more specific date and time information."
                        st.session_state['messages'].append({"role": "assistant", "content": assistant_response})
                        with st.chat_message("assistant"):
                            st.write(assistant_response)
                        return
                    
                    # Create the event
                    result = create_calendar_event(calendar_service, extracted_json)
                    
                    if result.get("success"):
                        assistant_response = f"""
                        ✅ Event created successfully!
                        
                        📌 Title: {extracted_json.get('summary')}
                        🕒 When: {extracted_json.get('start', {}).get('dateTime')} to {extracted_json.get('end', {}).get('dateTime')}
                        📍 Where: {extracted_json.get('location', 'No location specified')}
                        🔗 Calendar Link: {result.get('link')}
                        """
                    else:
                        assistant_response = f"❌ Failed to create event: {result.get('error')}"
                else:
                    assistant_response = "❌ Not able to get the time or details are incomplete. Please provide more specific date and time information."
            
            # Add assistant response to chat history
            st.session_state['messages'].append({"role": "assistant", "content": assistant_response})
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(assistant_response)
    
    # Add a button to list upcoming events
    if st.button("List Upcoming Events"):
        with st.spinner("Fetching your upcoming events..."):
            events_result = list_upcoming_events(calendar_service)
            if events_result.get("success"):
                events_list = events_result.get("events")
                if events_list:
                    st.subheader("Your Upcoming Events")
                    for event in events_list:
                        st.write(event)
                else:
                    st.info("No upcoming events found.")
            else:
                st.error(f"Error fetching events: {events_result.get('error')}")

if __name__ == '__main__':
    main()