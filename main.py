import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from typing import List, Dict
import json

class YouTubeMigrator:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube.force-ssl'
        ]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.client_secrets_file = "client_secrets.json"
        self.source_credentials = None
        self.destination_credentials = None
        
    def authenticate_account(self, is_source: bool = True) -> None:
        """Authenticate a YouTube account."""
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow
        # Allow insecure local host for development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file, self.scopes)
            
        account_type = "source" if is_source else "destination"
        print(f"\nAuthenticating {account_type} account...")
        print("A browser window will open for authentication...")
        
        try:
            credentials = flow.run_local_server(port=0)
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise
        
        if is_source:
            self.source_credentials = credentials
        else:
            self.destination_credentials = credentials
            
    def get_youtube_service(self, credentials):
        """Create YouTube API service instance."""
        return googleapiclient.discovery.build(
            self.api_service_name, 
            self.api_version, 
            credentials=credentials
        )
        
    def get_playlists(self, service, playlist_names: List[str]) -> List[Dict]:
        """Get specified playlists from account."""
        playlists = []
        
        try:
            request = service.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50
            )
            response = request.execute()
            
            # Filter playlists by provided names
            for item in response.get('items', []):
                if item['snippet']['title'] in playlist_names:
                    playlists.append({
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'id': item['id']
                    })
                    
            return playlists
            
        except googleapiclient.errors.HttpError as e:
            print(f"Error getting playlists: {e}")
            return []
            
    def get_playlist_items(self, service, playlist_id: str) -> List[Dict]:
        """Get all videos from a playlist."""
        items = []
        next_page_token = None
        
        while True:
            try:
                request = service.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    items.append({
                        'videoId': item['snippet']['resourceId']['videoId'],
                        'position': item['snippet']['position']
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except googleapiclient.errors.HttpError as e:
                print(f"Error getting playlist items: {e}")
                break
                
        return items
        
    def create_playlist(self, service, title: str, description: str) -> str:
        """Create a new playlist and return its ID."""
        try:
            request = service.playlists().insert(
                part="snippet",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    }
                }
            )
            response = request.execute()
            return response['id']
            
        except googleapiclient.errors.HttpError as e:
            print(f"Error creating playlist: {e}")
            return None
            
    def add_video_to_playlist(self, service, playlist_id: str, video_id: str, position: int) -> bool:
        """Add a video to a playlist."""
        try:
            request = service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        },
                        "position": position
                    }
                }
            )
            request.execute()
            return True
            
        except googleapiclient.errors.HttpError as e:
            print(f"Error adding video to playlist: {e}")
            return False
            
    def get_subscriptions(self, service) -> List[Dict]:
        """Get all subscriptions from account."""
        subscriptions = []
        next_page_token = None
        
        while True:
            try:
                request = service.subscriptions().list(
                    part="snippet",
                    mine=True,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    subscriptions.append({
                        'channelId': item['snippet']['resourceId']['channelId'],
                        'title': item['snippet']['title']
                    })
                    
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except googleapiclient.errors.HttpError as e:
                print(f"Error getting subscriptions: {e}")
                break
                
        return subscriptions
        
    def subscribe_to_channel(self, service, channel_id: str) -> bool:
        """Subscribe to a channel."""
        try:
            request = service.subscriptions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": channel_id
                        }
                    }
                }
            )
            request.execute()
            return True
            
        except googleapiclient.errors.HttpError as e:
            print(f"Error subscribing to channel: {e}")
            return False
            
    def migrate_playlists(self, playlist_names: List[str]) -> None:
        """Migrate specified playlists from source to destination account."""
        source_service = self.get_youtube_service(self.source_credentials)
        dest_service = self.get_youtube_service(self.destination_credentials)
        
        # Get playlists from source account
        source_playlists = self.get_playlists(source_service, playlist_names)
        
        for playlist in source_playlists:
            print(f"\nMigrating playlist: {playlist['title']}")
            
            # Create playlist in destination account
            new_playlist_id = self.create_playlist(
                dest_service,
                playlist['title'],
                playlist['description']
            )
            
            if new_playlist_id:
                # Get videos from source playlist
                videos = self.get_playlist_items(source_service, playlist['id'])
                
                # Add videos to new playlist
                for video in videos:
                    success = self.add_video_to_playlist(
                        dest_service,
                        new_playlist_id,
                        video['videoId'],
                        video['position']
                    )
                    if success:
                        print(f"Added video at position {video['position']}")
                    else:
                        print(f"Failed to add video at position {video['position']}")
                        
    def migrate_subscriptions(self) -> None:
        """Migrate all subscriptions from source to destination account."""
        source_service = self.get_youtube_service(self.source_credentials)
        dest_service = self.get_youtube_service(self.destination_credentials)
        
        # Get subscriptions from both accounts
        source_subscriptions = self.get_subscriptions(source_service)
        dest_subscriptions = self.get_subscriptions(dest_service)

        # Filter out already subscribed channels
        subscriptions = [
            source_sub
            for source_sub in source_subscriptions
            if not any(
                target_sub["channelId"] == source_sub["channelId"]
                for target_sub in dest_subscriptions
            )
        ]

        print(f"\nMigrating {len(subscriptions)} subscriptions...")
        for sub in subscriptions:
            success = self.subscribe_to_channel(dest_service, sub['channelId'])
            if success:
                print(f"Subscribed to: {sub['title']}")
            else:
                print(f"Failed to subscribe to: {sub['title']}")

def main():
    # Initialize migrator
    migrator = YouTubeMigrator()
    
    # Authenticate both accounts
    print("Please authenticate your source YouTube account...")
    migrator.authenticate_account(is_source=True)
    
    print("\nPlease authenticate your destination YouTube account...")
    migrator.authenticate_account(is_source=False)
    
    # Get playlist names to migrate
    playlist_names = input("\nEnter playlist names to migrate (comma-separated): ").split(',')
    playlist_names = [name.strip() for name in playlist_names]
    
    # Perform migration
    print("\nStarting playlist migration...")
    migrator.migrate_playlists(playlist_names)
    
    # Migrate subscriptions
    migrate_subs = input("\nDo you want to migrate subscriptions? (y/n): ").lower()
    if migrate_subs == 'y':
        migrator.migrate_subscriptions()
    
    print("\nMigration complete!")

if __name__ == "__main__":
    main()