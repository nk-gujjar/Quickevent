# Description: Utility functions for interacting with Google Calendar API.

import os
import datetime as dt
import logging
import re
from typing import Dict, List, Any, Optional
import json
import time
import pickle
import streamlit as st
import logging

# Set up logging
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
# # Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# logger = logging.getLogger(__name__)
# Suppress the oauth2client warning by setting a specific environment variable
# This is a temporary fix until migrating fully away from file_cache
os.environ['OAUTH_SKIP_CACHE_WARNING'] = '1'

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar API Scope
SCOPES = ['https://www.googleapis.com/auth/calendar']


# Set default timezone to Indian Standard Time
DEFAULT_TIMEZONE = "Asia/Kolkata"  # Indian Standard Time (IST)
DEFAULT_TIMEZONE_OFFSET = "+05:30"  # UTC+5:30 for India

# def get_credentials():
#     """Handles Google Calendar API credentials securely with improved error handling."""
#     creds = None

#     if os.path.exists("token.json"):
#         try:
#             creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#         except Exception as e:
#             logging.warning(f"❗ Corrupted token.json file detected: {str(e)}. Deleting and re-authenticating...")
#             os.remove("token.json")  # Delete the corrupted token file

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             try:
#                 creds.refresh(Request())
#             except Exception as e:
#                 logging.warning(f"❗ Token refresh failed: {str(e)}. Re-authenticating from scratch...")
#                 if os.path.exists("token.json"):
#                     os.remove("token.json")  # Delete the corrupted token file
#                 return get_credentials()  # Restart credential fetching
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())

#     return creds
def get_credentials():
    """
    Gets valid credentials for the Google Calendar API.

    Priority order:
    1. Streamlit secrets (deployed apps)
    2. Environment variables
    3. Local token.json file (if exists)
    4. Local credentials.json file (fallback)

    Returns:
        Google OAuth2 credentials object
    """
    creds = None

    # 1️⃣ **Use token from session_state (if available)**
    if "token" in st.session_state:
        logger.info("Using token from session state")
        creds = Credentials.from_authorized_user_info(st.session_state["token"], SCOPES)

    # 2️⃣ **Use token.json (if exists)**
    elif os.path.exists("token.json"):
        logger.info("Loading credentials from token.json")
        with open("token.json", "r") as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)

    # If credentials don't exist or are invalid
    if not creds or not creds.valid:
        # Refresh if possible
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            try:
                # 3️⃣ **Streamlit secrets (recommended for deployment)**
                if "google_credentials" in st.secrets:
                    logger.info("Loading credentials from Streamlit secrets")
                    client_config = json.loads(st.secrets["google_credentials"])  # Ensure it's parsed correctly
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)

                # 4️⃣ **Environment variable (alternative approach)**
                elif "GOOGLE_CREDENTIALS" in os.environ:
                    logger.info("Loading credentials from environment variable")
                    client_config = json.loads(os.environ["GOOGLE_CREDENTIALS"])
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)

                # 5️⃣ **Local credentials.json file (fallback)**
                elif os.path.exists("credentials.json"):
                    logger.info("Loading credentials from credentials.json file")
                    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                    creds = flow.run_local_server(port=0)
                
                else:
                    error_msg = "No credentials found! Please set up credentials through Streamlit secrets or environment variables."
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

            except Exception as e:
                logger.error(f"Error during authentication: {str(e)}")
                raise

        # Save the credentials for future use
        if creds:
            st.session_state["token"] = json.loads(creds.to_json())
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    return creds

def get_calendar_service():
    """Build and return the Google Calendar API service with retry logic."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            creds = get_credentials()
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            return service
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logging.error(f"Failed to build Calendar service after {max_retries} attempts: {str(e)}")
                raise
            else:
                logging.warning(f"Attempt {retry_count} failed to build Calendar service: {str(e)}. Retrying...")
                time.sleep(1)  # Wait before retrying

def parse_datetime(datetime_str: str) -> Optional[dt.datetime]:
    """
    Attempts to parse a datetime string in various formats.
    Returns None if parsing fails.
    """
    if not datetime_str:
        return None
    
    formats = [
        '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
        '%Y-%m-%dT%H:%M:%S',     # ISO format without timezone
        '%Y-%m-%d %H:%M:%S',     # Standard datetime format
        '%Y-%m-%d %H:%M',        # Date with time (no seconds)
        '%Y-%m-%d',              # Just date
        '%m/%d/%Y %H:%M:%S',     # US format with time
        '%m/%d/%Y %H:%M',        # US format with time (no seconds)
        '%m/%d/%Y',              # US date format
        '%d/%m/%Y %H:%M:%S',     # European/Indian format with time
        '%d/%m/%Y %H:%M',        # European/Indian format with time (no seconds)
        '%d/%m/%Y',              # European/Indian date format
    ]
    
    for fmt in formats:
        try:
            return dt.datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    # Try extracting with regex for natural language processing
    try:
        # Simple pattern for "March 18, 2025 at 3 PM" or similar
        match = re.search(r'(\w+ \d{1,2}, \d{4})(?:.+?(\d{1,2}(?::\d{2})? [AP]M))?', datetime_str)
        if match:
            date_part = match.group(1)
            time_part = match.group(2) if match.group(2) else "12:00 PM"
            return dt.datetime.strptime(f"{date_part} {time_part}", '%B %d, %Y %I:%M %p')
    except Exception:
        pass
    
    return None

def validate_event_data(event_data: Dict) -> Dict:
    """Validates and formats event data to ensure it's compatible with Google Calendar API."""
    # Create a copy to avoid modifying the original
    validated_event = event_data.copy()
    parsing_errors = []
    
    # Ensure required fields exist
    if 'summary' not in validated_event or not validated_event['summary']:
        validated_event['summary'] = "Untitled Event"
    
    # Get current year for validation
    current_year = dt.datetime.now().year
    
    # Validate start and end times
    for time_field in ['start', 'end']:
        if time_field not in validated_event:
            # If missing time fields, create with current time + 1 hour for start, + 2 hours for end
            now = dt.datetime.now()
            offset = 1 if time_field == 'start' else 2
            future_time = now + dt.timedelta(hours=offset)
            iso_time = future_time.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Add IST timezone
            iso_time = iso_time + DEFAULT_TIMEZONE_OFFSET
                
            validated_event[time_field] = {
                'dateTime': iso_time,
                'timeZone': DEFAULT_TIMEZONE
            }
        elif isinstance(validated_event[time_field], dict):
            # Ensure timeZone exists
            if 'timeZone' not in validated_event[time_field]:
                validated_event[time_field]['timeZone'] = DEFAULT_TIMEZONE
            
            # Check if dateTime exists and is valid
            if 'dateTime' in validated_event[time_field]:
                datetime_str = validated_event[time_field]['dateTime']
                
                if datetime_str:
                    try:
                        # Try to parse the datetime string
                        parsed_dt = parse_datetime(datetime_str)
                        
                        if parsed_dt is None:
                            # If parsing fails, log an error and use default time
                            parsing_errors.append(f"Could not parse {time_field} time: {datetime_str}")
                            
                            now = dt.datetime.now()
                            offset = 1 if time_field == 'start' else 2
                            future_time = now + dt.timedelta(hours=offset)
                            validated_event[time_field]['dateTime'] = future_time.strftime('%Y-%m-%dT%H:%M:%S') + DEFAULT_TIMEZONE_OFFSET
                        else:
                            # Fix year if it's in the past
                            if parsed_dt.year < current_year:
                                parsed_dt = parsed_dt.replace(year=current_year)
                            
                            # Format datetime in ISO format with timezone
                            validated_event[time_field]['dateTime'] = parsed_dt.strftime('%Y-%m-%dT%H:%M:%S') + DEFAULT_TIMEZONE_OFFSET
                    except Exception as e:
                        parsing_errors.append(f"Error parsing {time_field} time: {str(e)}")
                        
                        # Use default time if parsing fails
                        now = dt.datetime.now()
                        offset = 1 if time_field == 'start' else 2
                        future_time = now + dt.timedelta(hours=offset)
                        validated_event[time_field]['dateTime'] = future_time.strftime('%Y-%m-%dT%H:%M:%S') + DEFAULT_TIMEZONE_OFFSET
    
    # Validate attendees format if present
    if 'attendees' in validated_event and isinstance(validated_event['attendees'], list):
        for i, attendee in enumerate(validated_event['attendees']):
            if isinstance(attendee, str):
                # Convert string emails to proper format
                validated_event['attendees'][i] = {'email': attendee}
    
    return validated_event, parsing_errors

def create_calendar_event(service, event_data: Dict) -> Dict:
    """Creates an event on Google Calendar using the provided event data."""
    try:
        # Validate and format the event data
        validated_event, parsing_errors = validate_event_data(event_data)
        
        # Log the event data being sent
        logging.info(f"Creating event with data: {validated_event}")
        
        # Insert the event with retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                event = service.events().insert(calendarId="primary", body=validated_event).execute()
                
                # Log successful creation
                logging.info(f"Event created successfully with ID: {event.get('id')}")
                
                # Return success result with event link and any parsing errors
                result = {
                    "success": True,
                    "event_id": event.get('id'),
                    "link": event.get('htmlLink')
                }
                
                if parsing_errors:
                    result["warnings"] = parsing_errors
                    result["message"] = "Event created with some time parsing issues. Default times were used."
                
                return result
            
            except HttpError as error:
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error(f"Failed to create event after {max_retries} attempts: {error}")
                    return {
                        "success": False,
                        "error": str(error),
                        "warnings": parsing_errors if parsing_errors else None
                    }
                else:
                    logging.warning(f"Attempt {retry_count} failed to create event: {error}. Retrying...")
                    time.sleep(1)  # Wait before retrying
    
    except Exception as e:
        logging.error(f"Unexpected error creating event: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "warnings": parsing_errors if 'parsing_errors' in locals() else None
        }

def list_upcoming_events(service) -> Dict:
    """Lists the next 10 upcoming events with timeout handling."""
    now = dt.datetime.utcnow().isoformat() + "Z"
    
    try:
        # Set a timeout for the API request
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                events_result = (
                    service.events()
                    .list(
                        calendarId="primary",
                        timeMin=now,
                        maxResults=10,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                
                events = events_result.get("items", [])
                events_list = []
                
                if not events:
                    return {"success": True, "events": [], "message": "No upcoming events found."}
                
                for event in events:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    try:
                        # Format the date nicely if possible
                        if 'T' in start:  # If it includes time
                            start_dt = dt.datetime.fromisoformat(start.replace('Z', '+00:00'))
                            formatted_start = start_dt.strftime('%B %d, %Y at %I:%M %p')
                        else:  # All-day event
                            start_dt = dt.datetime.fromisoformat(start)
                            formatted_start = start_dt.strftime('%B %d, %Y (all day)')
                    except:
                        formatted_start = start  # Use original if parsing fails
                        
                    events_list.append(f"🕒 {formatted_start} - {event['summary']}")
                
                return {"success": True, "events": events_list}
            
            except HttpError as error:
                if "timed out" in str(error).lower():
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.error(f"Request timed out after {max_retries} attempts")
                        return {
                            "success": False, 
                            "error": "The request to fetch calendar events timed out. Please try again later."
                        }
                    else:
                        logging.warning(f"Attempt {retry_count} timed out. Retrying...")
                        time.sleep(2)  # Increase wait time before retrying
                else:
                    logging.error(f"HTTP error while fetching events: {error}")
                    return {"success": False, "error": str(error)}
            
            except Exception as e:
                logging.error(f"Unexpected error in attempt {retry_count}: {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    break
                time.sleep(1)
    
    except Exception as e:
        logging.error(f"Unexpected error listing events: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def format_event_time_indian(event_data: Dict) -> Dict:
    """
    Ensures all event times are properly formatted for Indian timezone.
    Use this function before sending event data to create_calendar_event.
    """
    event_copy = event_data.copy()
    
    # Format start and end times for Indian timezone
    for time_field in ['start', 'end']:
        if time_field in event_copy:
            if isinstance(event_copy[time_field], dict):
                # Set the timezone to Indian Standard Time
                event_copy[time_field]['timeZone'] = DEFAULT_TIMEZONE
                
                # Ensure dateTime is properly formatted with IST timezone offset
                if 'dateTime' in event_copy[time_field]:
                    date_str = event_copy[time_field]['dateTime']
                    
                    # Try to parse the existing datetime
                    try:
                        parsed_dt = parse_datetime(date_str)
                        if parsed_dt:
                            # Format with IST timezone offset
                            event_copy[time_field]['dateTime'] = parsed_dt.strftime('%Y-%m-%dT%H:%M:%S') + DEFAULT_TIMEZONE_OFFSET
                    except:
                        # If parsing fails, use current time + offset
                        now = dt.datetime.now()
                        offset = 1 if time_field == 'start' else 2
                        future_time = now + dt.timedelta(hours=offset)
                        event_copy[time_field]['dateTime'] = future_time.strftime('%Y-%m-%dT%H:%M:%S') + DEFAULT_TIMEZONE_OFFSET
            else:
                # If the time field is not a dict, create a proper structure
                now = dt.datetime.now()
                offset = 1 if time_field == 'start' else 2
                future_time = now + dt.timedelta(hours=offset)
                event_copy[time_field] = {
                    'dateTime': future_time.strftime('%Y-%m-%dT%H:%M:%S') + DEFAULT_TIMEZONE_OFFSET,
                    'timeZone': DEFAULT_TIMEZONE
                }
    
    return event_copy