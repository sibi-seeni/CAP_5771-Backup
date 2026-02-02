import os
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from .database import SessionLocal, Video, CollectionState

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
KEYWORDS = ["Arc Raiders", "Arc Raiders gameplay", "Arc Raiders review", "#ArcRaiders", "ARC RAIDERS", "arc raiders"]

def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

def search_new_videos():
    youtube = get_youtube_client()
    db: Session = SessionLocal()

    # Tracking IDs added in this session to prevent internal collisions
    added_this_session = set()
    
    for keyword in KEYWORDS:
        state = db.query(CollectionState).filter_by(keyword=keyword).first()
        
        if not state:
            last_search = datetime(2025, 10, 30)
            state = CollectionState(keyword=keyword, last_search_time=last_search)
            db.add(state)
        else:
            last_search = state.last_search_time

        published_after = last_search.strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"Searching for '{keyword}' after {published_after}...")

        next_page_token = None
        while True:
            request = youtube.search().list(
                q=keyword,
                part="snippet",
                type="video",
                order="date",
                publishedAfter=published_after,
                videoCategoryId="20",
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                
                # UPDATED LOGIC: Check both DB and the local session set
                if video_id not in added_this_session:
                    exists = db.query(Video).filter_by(video_id=video_id).first()
                    if not exists:
                        new_video = Video(
                            video_id=video_id,
                            title=item["snippet"]["title"],
                            description=item["snippet"]["description"],
                            channel_id=item["snippet"]["channelId"],
                            published_at=datetime.strptime(item["snippet"]["publishedAt"], '%Y-%m-%dT%H:%M:%SZ'),
                            keyword_matched=keyword
                        )
                        db.add(new_video)
                        added_this_session.add(video_id) # Tracking it locally

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        # Commit after each keyword to clear the memory and save progress
        state.last_search_time = datetime.utcnow()
        db.commit()

    db.close()
    print("Discovery Phase Complete.")

if __name__ == "__main__":
    search_new_videos()