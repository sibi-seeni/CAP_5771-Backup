import logging
import os
from dotenv import load_dotenv
from src import init_db, search_new_videos, collect_comments, load_data, analyze_sentiment, plot_sentiment_over_time

# 1. Environment Check
load_dotenv()

def check_config():
    """Ensures the environment is ready for an academic run."""
    if not os.getenv("YOUTUBE_API_KEY"):
        print("CRITICAL ERROR: YOUTUBE_API_KEY not found in .env file.")
        return False
    return True

# 2. Setup Logging
logging.basicConfig(
    filename='collection_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_pipeline():
    if not check_config():
        return

    logging.info("--- Starting Full Pipeline Run ---")
    print("Starting Arc Raiders Sentiment Analysis Pipeline...")
    
    try:
        # Step 0: Infrastructure
        init_db()
        
        # Step 1: Data Acquisition (Phases 2 & 3)
        logging.info("Phase 2 & 3: Acquiring Data...")
        search_new_videos()
        collect_comments()
        
        # Step 2: Data Science & Analysis (Phase 6)
        logging.info("Phase 6: Running Sentiment Analysis...")
        print("Analyzing collected data and generating plots...")
        
        data = load_data()
        if not data.empty:
            analyzed_data = analyze_sentiment(data)
            plot_sentiment_over_time(analyzed_data)
            
            # Export final result for the methods section
            analyzed_data.to_csv('arc_raiders_final_analysis.csv')
            logging.info(f"Analysis complete. Total records: {len(analyzed_data)}")
            print(f"Pipeline complete! Processed {len(analyzed_data)} comments.")
        else:
            logging.warning("No data found for analysis in this run.")
            print("No data found to analyze.")

        logging.info("--- Full Pipeline Run Successful ---")

    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        print(f"Pipeline encountered an error. Check logs for details.")

if __name__ == "__main__":
    run_pipeline()