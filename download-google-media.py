# Import the required libraries
import io
import os
import datetime
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import traceback
import logging

# Define the scopes for accessing the APIs
SCOPES = [    
    'https://www.googleapis.com/auth/photoslibrary',
    'https://www.googleapis.com/auth/photoslibrary.readonly',
    'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.photos.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]

# Create a function to authorize the access to the APIs
def authorize():
    # Check if the credentials file exists
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Create a function to get the media items from Google Photos for a given date range
def get_media_items(start_date, end_date):
    # Build the service object for the Google Photos Library API
    service = build('photoslibrary', 'v1', credentials=authorize(), static_discovery=False)
    # Create a filter object with the date range
    filters = {
        "dateFilter": {
            "ranges": [
                {
                    "startDate": {
                        "year": start_date.year,
                        "month": start_date.month,
                        "day": start_date.day
                    },
                    "endDate": {
                        "year": end_date.year,
                        "month": end_date.month,
                        "day": end_date.day
                    }
                }
            ]
        }
    }
    # Create a request object with the filter
    request = service.mediaItems().search(body={"filters": filters})
    # Initialize an empty list to store the media items
    media_items = []
    # Loop through the pages of the response
    while request is not None:
        response = request.execute()
        # Append the media items to the list
        media_items.extend(response.get('mediaItems', []))
        # Get the next page token
        request = service.mediaItems().list_next(request, response)
    return media_items

# Create a function to download the media items from Google Drive to a local folder
def download_media_items(media_items, folder):
    # Build the service object for the Google Drive API
    service = build('drive', 'v3', credentials=authorize())
    c = 0
    # Loop through the media items
    for item in media_items:
        try:
                
            c += 1
            
            # Get the file id and name from the item
            file_name = item['filename']                
            file_path = os.path.join(folder, file_name)
            if os.path.exists(file_path):
                print(f"{file_path} exists")
                continue
                            
            download_flag =  ''
            mime_type = item['mimeType']
            if mime_type.startswith("image"):
                download_flag = '=d'
            elif mime_type.startswith("video"):
                download_flag = '=dv'            
            download_url = item['baseUrl'] + download_flag                
            # Create a request object to get the file content
            content = requests.get(download_url).content
            # Create a file handle to write the file content
            with open(file_path, 'wb') as f:
                f.write(content)
                print(f"Downloaded {file_name}: {c} of {len(media_items)}")   
                
        except Exception as e:
            logging.error(traceback.format_exc())
        

# Define the start and end dates for the date range
start_date = datetime.date(2023, 4, 1)
end_date = datetime.date(2023, 12, 31)
print (f"Download files {start_date} - {end_date}")
# Define the local folder to save the downloaded files
folder = './images'

# Get the media items for the date range
media_items = get_media_items(start_date, end_date)

# Download the media items to the local folder
download_media_items(media_items, folder)
