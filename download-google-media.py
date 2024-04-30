# Import the required libraries
import datetime
import calendar
import argparse
import os
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import traceback
import logging

def main(start_date: datetime.date, end_date: datetime.date, folder: str):    
    # Define the scopes for accessing the APIs
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

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
        # Google cloud api authorize
        creds = authorize()
        
        print("photoslibrary api request...")
        # Build the service object for the Google Photos Library API
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
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
        request = service.mediaItems().search(body={"filters": filters, "pageSize": 100})    
        
        # Initialize an empty list to store the media items
        media_items = []
        # Loop through the pages of the response
        while request is not None:        
            response = request.execute()        
            # Append the media items to the list
            media_items.extend(response.get('mediaItems', []))
            # Get the next page token
            request = service.mediaItems().list_next(request, response)
            print(f"{len(media_items)} media items found.")
        
        return media_items

    # Create a function to download the media items from Google Drive to a local folder
    def download_media_items(media_items, folder):
        # Build the service object for the Google Drive API    
        c = 0
        # Loop through the media items
        for item in media_items:
            try:
                    
                c += 1
                
                # Get the file id and name from the item
                file_name = item['filename']                
                file_path = os.path.join(folder, file_name)
                if os.path.exists(file_path):
                    print(f"{file_name} exists: {c} of {len(media_items)}")
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
            
    print (f"Download files {start_date} - {end_date} to {folder}")

    # Get the media items for the date range
    media_items = get_media_items(start_date, end_date)

    # Download the media items to the local folder
    download_media_items(media_items, folder)

def parse_args():
    today = datetime.date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('--start-date', help='A required end date of range', nargs='?', default=str(first_day))
    parser.add_argument('--end-date', help='A required end date of range', nargs='?', default=str(last_day))
    parser.add_argument('--folder', help='Target folder', nargs='?', default='./images')
    args = parser.parse_args()
    
    start_date = datetime.date.fromisoformat(args.start_date)
    end_date = datetime.date.fromisoformat(args.end_date)
    folder = args.folder
    
    if start_date > end_date:
        (start_date, end_date) = (end_date, start_date)
    if (end_date - start_date).days > 366:
        print(f"Date range can't be longer than 365 days.")
        exit()
        
    if not os.path.exists(folder) or not os.path.isdir(folder):
        print(f"Folder {folder} does not exists.")
        exit()
    return start_date, end_date, folder

if __name__ == "__main__":
    start_date, end_date, folder = parse_args()            
    main(start_date=start_date, end_date=end_date, folder=folder)