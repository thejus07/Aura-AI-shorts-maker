import os
import logging
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config import CREDENTIALS_FILE, TOKEN_FILE

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Upload scopes required to post videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeUploader:
    def __init__(self):
        self.credentials = None

    def get_auth_status(self) -> dict:
        """
        Checks the status of OAuth authentication.
        Returns a dictionary indicating if credentials file is present, and if the user is authenticated.
        """
        secrets_exist = CREDENTIALS_FILE.exists()
        token_exists = TOKEN_FILE.exists()
        
        authenticated = False
        if token_exists:
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                if creds and creds.valid:
                    authenticated = True
                elif creds and creds.expired and creds.refresh_token:
                    # Attempt a silent refresh to verify
                    creds.refresh(Request())
                    authenticated = creds.valid
            except Exception:
                authenticated = False

        return {
            "client_secrets_configured": secrets_exist,
            "authenticated": authenticated,
            "credentials_path": str(CREDENTIALS_FILE),
            "token_path": str(TOKEN_FILE)
        }

    def authenticate(self, run_interactive: bool = False) -> bool:
        """
        Attempts to load credentials from token.json. 
        If expired, refreshes it.
        If missing and run_interactive is True, starts OAuth browser flow.
        """
        creds = None
        
        # 1. Try to load from saved token file
        if TOKEN_FILE.exists():
            try:
                logging.info("Loading YouTube credentials from cache token...")
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except Exception as e:
                logging.error(f"Error reading token file: {e}. Re-authenticating needed.")

        # 2. If token is invalid or expired, refresh it
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    logging.info("Refreshing expired YouTube credentials token...")
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(TOKEN_FILE, "w") as token:
                        token.write(creds.to_json())
                    logging.info("YouTube credentials token refreshed successfully.")
                except Exception as e:
                    logging.error(f"Failed to refresh YouTube credentials: {e}")
                    creds = None
            else:
                creds = None

        # 3. If no cached/refreshed creds, and we are allowed to be interactive, run OAuth login
        if not creds:
            if not CREDENTIALS_FILE.exists():
                logging.error(f"YouTube client_secret.json missing at: {CREDENTIALS_FILE}")
                return False
                
            if run_interactive:
                try:
                    logging.info("Launching YouTube OAuth 2.0 Web Authentication flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(CREDENTIALS_FILE), 
                        scopes=SCOPES
                    )
                    # Opens standard local browser port for user to sign in
                    creds = flow.run_local_server(port=0, authorization_prompt_message="Please authorize this app to upload shorts to your channel.")
                    
                    # Save credentials for future headless runs
                    with open(TOKEN_FILE, "w") as token:
                        token.write(creds.to_json())
                    logging.info("Successfully authenticated and cached token.json credentials.")
                except Exception as e:
                    logging.error(f"YouTube OAuth interactive authentication failed: {e}")
                    return False
            else:
                logging.info("Headless authentication attempted but no cached credentials available.")
                return False

        self.credentials = creds
        return creds is not None and creds.valid

    def upload_video(self, video_path: str, title: str, description: str, tags: list = None, privacy_status: str = "private", progress_callback=None) -> str:
        """
        Uploads a video to YouTube.
        - privacy_status: 'public', 'private', or 'unlisted'
        - progress_callback: a callable function taking float (0.0 to 1.0) representing progress
        Returns the YouTube Video ID on success.
        """
        if not self.authenticate(run_interactive=False):
            raise PermissionError("YouTube account is not authenticated. Please run authentication via dashboard first.")

        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file to upload does not exist: {video_path}")

        # Ensure #shorts is in the title or description to trigger YouTube Shorts categorizer
        shorts_tag = "#shorts"
        if shorts_tag.lower() not in title.lower() and shorts_tag.lower() not in description.lower():
            title = f"{title} {shorts_tag}"

        try:
            # Build YouTube service
            youtube = build("youtube", "v3", credentials=self.credentials)
            
            body = {
                "snippet": {
                    "title": title[:100], # YouTube limit
                    "description": description[:5000], # YouTube limit
                    "tags": tags or ["shorts", "ai", "contentcreator"],
                    "categoryId": "22" # 'People & Blogs' category
                },
                "status": {
                    "privacyStatus": privacy_status, # 'private', 'public', 'unlisted'
                    "selfDeclaredMadeForKids": False
                }
            }

            logging.info(f"Initializing upload of video: '{video_path}'...")
            media = MediaFileUpload(
                video_path, 
                chunksize=1024 * 1024, # 1MB chunks
                resumable=True, 
                mimetype="video/mp4"
            )
            
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            # Upload chunk-by-chunk to track and show progress
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = float(status.progress())
                    logging.info(f"Uploading Video: {int(progress * 100)}% complete.")
                    if progress_callback:
                        progress_callback(progress)
            
            video_id = response.get("id")
            logging.info(f"Upload completed successfully! YouTube Video ID: {video_id}")
            if progress_callback:
                progress_callback(1.0)
                
            return video_id
            
        except Exception as e:
            logging.error(f"Error uploading video to YouTube: {e}")
            raise RuntimeError(f"YouTube upload failed: {str(e)}")

# Test block
if __name__ == "__main__":
    pass
