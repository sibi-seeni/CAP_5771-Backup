import logging
from src import init_db, collect_comments

# Setting up Logging
logging.basicConfig(
    filename="collection_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s")

def run_pipeline():
    logging.info("--- Starting Comment Collection Run ---")

    try:
        # Phase 1: Ensure DB exists
        logging.info("Initializing Database...")
        init_db()
        logging.info("Database Ready.")

        # Phase 2: Comment Collection
        logging.info("Phase 2: Starting Comment Collection...")
        # Note: Each 'commentThreads.list' call costs 1 API quota unit
        collect_comments()
        logging.info("Phase 2 Complete.")

        logging.info("--- Comment Collection Successful ---")
        print("Comment collection executed successfully. Check collection_log.txt for details.")

    except Exception as e:
        logging.error(f"Critical error during comment collection: {e}")
        print(f"Comment collection failed. Error logged: {e}")

if __name__ == "__main__":
    run_pipeline()