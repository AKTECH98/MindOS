"""
Google Calendar Authentication Script
Run this script to authenticate and generate a new token.json file.
"""
import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TOKEN_FILE, CALENDAR_SCOPE

SCOPES = CALENDAR_SCOPE


def authenticate():
    """Run the OAuth flow to authenticate and save credentials."""
    creds = None
    
    # Check if token exists
    if TOKEN_FILE.exists():
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"Error loading existing token: {e}")
            print("Will proceed with new authentication...")
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
                save_credentials(creds)
                print("✅ Token refreshed successfully!")
                return
            except Exception as e:
                print(f"Error refreshing token: {e}")
                print("Need to re-authenticate...")
        
        # Check for credentials.json
        credentials_file = Path(__file__).parent.parent / "secrets" / "credentials.json"
        if not credentials_file.exists():
            print("❌ Error: credentials.json not found!")
            print(f"Please download your OAuth 2.0 credentials from Google Cloud Console")
            print(f"and save them as: {credentials_file}")
            print("\nSteps:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Select your project")
            print("3. Go to APIs & Services > Credentials")
            print("4. Create OAuth 2.0 Client ID (Desktop app)")
            print("5. Download and save as credentials.json in the secrets/ folder")
            return
        
        print("Starting OAuth flow...")
        print("A browser window will open. Please sign in and authorize the app.")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_file), SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # Save credentials
        save_credentials(creds)
        print(f"✅ Authentication successful! Token saved to {TOKEN_FILE}")
    else:
        print("✅ Valid credentials already exist!")


def save_credentials(creds):
    """Save credentials to token file."""
    # Ensure secrets directory exists
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
    }
    
    # Add expiry if available
    if creds.expiry:
        token_data['expiry'] = creds.expiry.isoformat()
    
    with open(TOKEN_FILE, 'w') as token:
        json.dump(token_data, token, indent=2)


if __name__ == "__main__":
    print("=" * 60)
    print("Google Calendar Authentication")
    print("=" * 60)
    authenticate()

