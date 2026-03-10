import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import time
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from .database import SessionLocal, Video, Comment # Removed the . for local execution compatibility

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

def anonymize_id(user_id):
    if not user_id: return "anonymous"
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()

# --- NEW HELPER FUNCTION TO STANDARDIZE SAVING ---
def save_comment(db, video_id, snippet, comment_id, added_in_video, parent_id=None):
    """
    Standardizes the saving process for both top-level comments and replies.
    """
    if comment_id not in added_in_video:
        exists = db.query(Comment).filter_by(comment_id=comment_id).first()
        if not exists:
            db.add(Comment(
                comment_id=comment_id,
                video_id=video_id,
                parent_id=parent_id, # Stores the ID of the original comment if this is a reply
                author_hash=anonymize_id(snippet.get("authorDisplayName")),
                text=snippet["textDisplay"],
                like_count=snippet.get("likeCount", 0),
                published_at=datetime.strptime(snippet["publishedAt"], '%Y-%m-%dT%H:%M:%SZ'),
                last_updated_at=datetime.strptime(snippet["updatedAt"], '%Y-%m-%dT%H:%M:%SZ')
            ))
            added_in_video.add(comment_id)
# ------------------------------------------------

def collect_comments():
    youtube = get_youtube_client()
    db: Session = SessionLocal()
    
    videos = db.query(Video).filter(Video.comments_disabled == False).all()
    
    for video in videos:
        print(f"Collecting comments and replies from: {video.title}")
        next_page_token = None
        added_in_video = set()
        
        try:
            while True:
                # --- UPDATED: Added 'replies' to part ---
                request = youtube.commentThreads().list(
                    part="snippet,replies", 
                    videoId=video.video_id,
                    maxResults=50,
                    order="time",
                    pageToken=next_page_token,
                    textFormat="plainText"
                )
                response = request.execute()
                time.sleep(0.1)  # prevents hitting rate limits

                for item in response.get("items", []):
                    # 1. Process Top Level Comment
                    top_comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
                    top_comment_id = item["snippet"]["topLevelComment"]["id"]
                    
                    save_comment(db, video.video_id, top_comment_snippet, top_comment_id, added_in_video)

                    # --- NEW: Process Nested Replies ---
                    if "replies" in item:
                        for reply in item["replies"]["comments"]:
                            reply_snippet = reply["snippet"]
                            reply_id = reply["id"]
                            # Pass the top_comment_id as the parent_id
                            save_comment(db, video.video_id, reply_snippet, reply_id, added_in_video, parent_id=top_comment_id)
                    # -----------------------------------
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            # Save this video's comments before moving to the next one
            db.commit()
            
        except Exception as e:
            db.rollback() # Clear the transaction in case of error
            if "commentsDisabled" in str(e):
                print(f"Comments disabled for video {video.video_id}. Skipping.")
                video.comments_disabled = True
                db.commit()
            else:
                print(f"Error while collecting for {video.video_id}: {e}")

    db.close()
    print("Comment and Reply Collection Phase Completed.")

if __name__ == "__main__":
    collect_comments()
