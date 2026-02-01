#!/usr/bin/env python3
"""
Google Drive Manager

Handles all interactions with Google Drive:
- Upload Stage 1 outputs
- Download Stage 2 results
- Manage folder structure
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class GoogleDriveManager:
    """Manages Google Drive operations for the pipeline."""
    
    def __init__(self, token_file: Path, folder_name: str = "GenAI_Pipeline_Automation"):
        """
        Initialize Drive manager.
        
        Args:
            token_file: Path to token.json (from auth_setup.py)
            folder_name: Name of root folder on Drive
        """
        self.token_file = token_file
        self.folder_name = folder_name
        self.service = None
        self.root_folder_id = None
        self._init_service()
    
    def _init_service(self):
        """Initialize Google Drive API service."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            creds = Credentials(
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                token_uri=token_data['token_uri'],
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data['scopes']
            )
            
            # Refresh token if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update token file
                token_data['token'] = creds.token
                with open(self.token_file, 'w') as f:
                    json.dump(token_data, f)
            
            self.service = build('drive', 'v3')
            logger.info("✓ Google Drive service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            raise
    
    def ensure_root_folder(self) -> str:
        """
        Ensure root automation folder exists on Drive.
        Returns folder ID.
        """
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                pageSize=1,
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                self.root_folder_id = files[0]['id']
                logger.info(f"✓ Found existing folder: {self.folder_name}")
                return self.root_folder_id
            
            # Create folder if it doesn't exist
            file_metadata = {
                'name': self.folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            self.root_folder_id = folder.get('id')
            logger.info(f"✓ Created folder: {self.folder_name} (ID: {self.root_folder_id})")
            return self.root_folder_id
            
        except Exception as e:
            logger.error(f"Failed to ensure root folder: {e}")
            raise
    
    def upload_stage1_output(self, local_package_path: Path, timestamp: str) -> str:
        """
        Upload Stage 1 output package to Drive.
        
        Args:
            local_package_path: Local directory with Stage 1 outputs
            timestamp: Timestamp for versioning
            
        Returns:
            Path on Drive where files were uploaded
        """
        try:
            if not self.root_folder_id:
                self.ensure_root_folder()
            
            # Create inputs subfolder
            inputs_folder_id = self._ensure_subfolder("stage2_inputs", self.root_folder_id)
            
            # Create timestamped folder
            version_folder_id = self._ensure_subfolder(f"stage1_{timestamp}", inputs_folder_id)
            
            logger.info(f"Uploading Stage 1 output to Drive...")
            
            # Upload all files recursively
            for local_file in local_package_path.rglob('*'):
                if local_file.is_file():
                    # Calculate relative path
                    rel_path = local_file.relative_to(local_package_path)
                    
                    # Create parent folders if needed
                    current_folder_id = version_folder_id
                    for parent_dir in rel_path.parents[:-1]:
                        current_folder_id = self._ensure_subfolder(
                            parent_dir.name, current_folder_id
                        )
                    
                    # Upload file
                    self._upload_file(local_file, rel_path.name, current_folder_id)
            
            logger.info(f"✓ Upload completed")
            return f"{self.folder_name}/stage2_inputs/stage1_{timestamp}"
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    def download_stage2_output(self, output_folder_name: str, download_path: Path) -> bool:
        """
        Download Stage 2 outputs from Drive.
        
        Args:
            output_folder_name: Name of folder on Drive (e.g., 'stage2_outputs')
            download_path: Local path to download to
            
        Returns:
            True if successful
        """
        try:
            if not self.root_folder_id:
                self.ensure_root_folder()
            
            # Find outputs folder
            outputs_folder_id = self._find_subfolder(output_folder_name, self.root_folder_id)
            if not outputs_folder_id:
                logger.error(f"Output folder not found: {output_folder_name}")
                return False
            
            logger.info(f"Downloading Stage 2 outputs...")
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Recursively download all files
            self._download_folder(outputs_folder_id, download_path)
            
            logger.info(f"✓ Download completed to {download_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def _ensure_subfolder(self, folder_name: str, parent_id: str) -> str:
        """Ensure a subfolder exists, create if needed."""
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false",
                spaces='drive',
                pageSize=1,
                fields='files(id)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                return files[0]['id']
            
            # Create folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
            
        except Exception as e:
            logger.error(f"Failed to ensure subfolder {folder_name}: {e}")
            raise
    
    def _find_subfolder(self, folder_name: str, parent_id: str) -> Optional[str]:
        """Find a subfolder by name."""
        try:
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false",
                spaces='drive',
                pageSize=1,
                fields='files(id)'
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
            
        except Exception as e:
            logger.error(f"Failed to find subfolder {folder_name}: {e}")
            return None
    
    def _upload_file(self, local_path: Path, file_name: str, folder_id: str) -> str:
        """Upload a single file to Drive."""
        try:
            from googleapiclient.http import MediaFileUpload
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(str(local_path))
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            raise
    
    def _download_folder(self, folder_id: str, local_path: Path):
        """Recursively download a folder from Drive."""
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                pageSize=1000,
                fields='files(id, name, mimeType)'
            ).execute()
            
            for file in results.get('files', []):
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursive download
                    sub_path = local_path / file['name']
                    sub_path.mkdir(exist_ok=True)
                    self._download_folder(file['id'], sub_path)
                else:
                    # Download file
                    self._download_file(file['id'], file['name'], local_path)
                    
        except Exception as e:
            logger.error(f"Failed to download folder: {e}")
            raise
    
    def _download_file(self, file_id: str, file_name: str, local_path: Path):
        """Download a single file from Drive."""
        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io
            
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.FileIO(str(local_path / file_name), 'wb')
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
                
        except Exception as e:
            logger.error(f"Failed to download {file_name}: {e}")
            raise
