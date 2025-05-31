"""
Generate a pre-authorized token for deployment.
Run this script locally before deploying.
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

def generate_token():
    """Generate a token for deployment use."""
    creds = None
    
    # Check if token.json already exists
    if os.path.exists('token.json'):
        print("Loading existing token...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
        else:
            print("Creating new token...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Important: Use access_type='offline' to get refresh token
            creds = flow.run_local_server(
                port=8080,
                access_type='offline',
                prompt='consent'  # Force consent screen
            )
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Token saved to token.json")
    
    # Print the token info for secrets.toml
    token_info = json.loads(creds.to_json())
    
    print("\n" + "="*50)
    print("TOKEN FOR DEPLOYMENT")
    print("="*50)
    print("Copy this to your secrets.toml file under [google_token]:")
    print()
    
    for key, value in token_info.items():
        if isinstance(value, list):
            print(f'{key} = {json.dumps(value)}')
        else:
            print(f'{key} = "{value}"')
    
    print("\n" + "="*50)
    print("Or copy the entire token.json content:")
    print(json.dumps(token_info, indent=2))
    print("="*50)

if __name__ == '__main__':
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json not found!")
        print("Please make sure you have the credentials.json file in the current directory.")
        exit(1)
    
    generate_token()