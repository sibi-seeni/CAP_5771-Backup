import os
import hashlib
import logging
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from .database import SessionLocal, Video, Comment

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

def anonymize_id(user_id):
    if not user_id: return "anonymous"
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()

def collect_comments():
    youtube = get_youtube_client()
    db: Session = SessionLocal()
    
    videos = db.query(Video).filter(Video.comments_disabled == False).all()
    
    for video in videos:
        print(f"Collecting comments from: {video.title}")
        next_page_token = None
        # NEW: ID tracker to avoid duplicates within the same video
        added_in_video = set()
        
        try:
            while True:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video.video_id,
                    maxResults=100,
                    pageToken=next_page_token,
                    textFormat="plainText"
                )
                response = request.execute()

                for item in response.get("items", []):
                    top_comment = item["snippet"]["topLevelComment"]["snippet"]
                    comment_id = item["snippet"]["topLevelComment"]["id"]
                    
                    # Double check: locally (set) and in the database
                    if comment_id not in added_in_video:
                        exists = db.query(Comment).filter_by(comment_id=comment_id).first()
                        if not exists:
                            db.add(Comment(
                                comment_id=comment_id,
                                video_id=video.video_id,
                                author_hash=anonymize_id(top_comment.get("authorDisplayName")),
                                text=top_comment["textDisplay"],
                                published_at=datetime.strptime(top_comment["publishedAt"], '%Y-%m-%dT%H:%M:%SZ'),
                                last_updated_at=datetime.strptime(top_comment["updatedAt"], '%Y-%m-%dT%H:%M:%SZ')
                            ))
                            added_in_video.add(comment_id)
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            
            # Save this video's comments before moving to the next one
            db.commit()
            
        except Exception as e:
            db.rollback()  # Clear the transaction in case of error
            if "commentsDisabled" in str(e):
                print(f"Comments disabled for video {video.video_id}. Skipping.")
                video.comments_disabled = True
                db.commit()
            else:
                print(f"Error while collecting for {video.video_id}: {e}")

    db.close()
    print("Comment Collection Phase Completed.")

if __name__ == "__main__":
    collect_comments()