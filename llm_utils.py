import requests
import time
import json
import re
import logging
from typing import Dict, List, Any, Optional
import api_keys

# Groq API Configuration
GROQ_API_KEY = api_keys.GROQ_API_KEY
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def query_groq(messages: List[Dict], max_tokens: int = 1024, max_retries: int = 5, retry_delay: int = 10) -> Dict:
    """
    Query the Groq API with messages and get JSON response.
    """
    payload = {
        "model": "llama3-70b-8192",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_API_URL, headers=GROQ_HEADERS, json=payload)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                logging.warning(f"Model is loading. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logging.error(f"API request failed: Status code {response.status_code}, Response: {response.text}")
                return {"error": f"API request failed with status code {response.status_code}", "details": response.text}
        except Exception as e:
            logging.error(f"Exception during API request: {str(e)}")
            return {"error": f"An exception occurred: {str(e)}"}
    
    return {"error": "Max retries reached. Model is still loading or unavailable."}

def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Extract JSON data from text using regex.
    Handles different patterns and formats that might be returned by LLMs.
    """
    # Try to find JSON objects with standard regex
    json_pattern = r'({[\s\S]*})'
    match = re.search(json_pattern, text)
    
    if match:
        try:
            json_str = match.group(1)
            return json.loads(json_str)
        except json.JSONDecodeError:
            logging.warning("Failed to parse JSON with standard regex")
    
    # Try to find JSON objects with code block markers
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(code_block_pattern, text)
    
    if match:
        try:
            json_str = match.group(1)
            return json.loads(json_str)
        except json.JSONDecodeError:
            logging.warning("Failed to parse JSON from code block")
    
    # Try to extract event data directly if in a specific format
    # Look for patterns like "summary": "Meeting"
    event_data = {}
    field_patterns = {
        'summary': r'"?summary"?\s*:\s*"([^"]*)"',
        'location': r'"?location"?\s*:\s*"([^"]*)"',
        'description': r'"?description"?\s*:\s*"([^"]*)"',
    }
    
    for field, pattern in field_patterns.items():
        match = re.search(pattern, text)
        if match:
            event_data[field] = match.group(1)
    
    # Look for date and time information
    datetime_pattern = r'"?dateTime"?\s*:\s*"([^"]*)"'
    datetime_matches = re.findall(datetime_pattern, text)
    
    if datetime_matches and len(datetime_matches) >= 2:
        event_data['start'] = {'dateTime': datetime_matches[0], 'timeZone': 'America/Los_Angeles'}
        event_data['end'] = {'dateTime': datetime_matches[1], 'timeZone': 'America/Los_Angeles'}
    
    # If we extracted any event data fields, return them
    if event_data:
        logging.info(f"Extracted event data using field patterns: {event_data}")
        return event_data
    
    logging.warning("Could not extract any valid JSON data from text")
    return None

def normalize_datetime(date_str: str) -> str:
    """
    Normalize date/time strings to ISO format with timezone.
    Handles various common formats and ensures proper timezone.
    """
    # This is a placeholder for more complex datetime normalization
    # In a real implementation, you would use datetime parsing libraries
    # to handle various formats and standardize them
    
    # Simple example to ensure timezone exists
    if date_str and not (date_str.endswith('Z') or '+' in date_str[-6:] or '-' in date_str[-6:]):
        return date_str + '-07:00'  # Default to Pacific Time
    return date_str