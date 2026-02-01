#!/usr/bin/env python3
"""
ONE-TIME SETUP: Authenticate with Google Drive and Colab.

Run this script once to establish secure credentials for the pipeline.
Credentials are saved locally and reused for all subsequent runs.

Usage:
    python auth_setup.py
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict

try:
    from google.colab import auth as colab_auth
    from google.colab import drive
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
CONFIG_DIR = Path(__file__).parent.parent / "config"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"


def setup_credentials_windows() -> Dict:
    """
    Setup OAuth 2.0 credentials on Windows.
    
    This requires a 'credentials.json' file from Google Cloud Console.
    Follow these steps:
    1. Go to https://console.cloud.google.com/
    2. Create a new project or select existing one
    3. Enable Google Drive API
    4. Create OAuth 2.0 Desktop Application credentials
    5. Download credentials.json and place in automation/config/
    """
    
    print("\n" + "="*70)
    print("GOOGLE DRIVE AUTHENTICATION SETUP (Windows)")
    print("="*70)
    
    # Check if credentials.json exists
    if not CREDENTIALS_FILE.exists():
        print(f"\n⚠️  ERROR: credentials.json not found at {CREDENTIALS_FILE}")
        print("\nTo obtain credentials:")
        print("1. Visit: https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable 'Google Drive API'")
        print("4. Create OAuth 2.0 credentials (Desktop Application)")
        print("5. Download and save as: automation/config/credentials.json")
        sys.exit(1)
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # Save token for future use
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print(f"\n✅ Token saved to {TOKEN_FILE}")
        print("You can now run the pipeline automation without re-authenticating.")
        return token_data
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        sys.exit(1)


def verify_credentials() -> bool:
    """Verify that credentials are properly set up."""
    
    print("\n" + "="*70)
    print("VERIFYING GOOGLE DRIVE ACCESS")
    print("="*70)
    
    if not TOKEN_FILE.exists():
        print("⚠️  No token found. Running authentication...")
        setup_credentials_windows()
    
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        
        # Try to build a Drive service
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials as OAuth2Credentials
        
        creds = OAuth2Credentials(
            token=token_data['token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        # Refresh if needed
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        service = build('drive', 'v3')
        service.files().list(pageSize=1).execute()
        
        print("✅ Google Drive access verified!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        print("Please run authentication again or check your credentials.")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup authentication for GenAI pipeline")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing credentials")
    args = parser.parse_args()
    
    if args.verify_only:
        success = verify_credentials()
        sys.exit(0 if success else 1)
    else:
        setup_credentials_windows()
        verify_credentials()
        print("\n" + "="*70)
        print("SETUP COMPLETE!")
        print("="*70)
        print("\nYou can now run: python orchestrate_pipeline.py")
