import logging
from src import init_db, search_new_videos  # collect_comments removed

# Setting up Logging
# Stores logs in a file for documentation
logging.basicConfig(
    filename="collection_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s")


def run_pipeline():
    logging.info("--- Starting Video Discovery Run ---")

    try:
        # Phase 1: Ensure DB is initialized
        logging.info("Initializing Database...")
        init_db()
        logging.info("Database Ready.")

        # Phase 2: Video Discovery
        logging.info("Phase 2: Starting Video Discovery...")
        # Note to self: Each 'search.list' call costs 100 quota units
        search_new_videos()
        logging.info("Phase 2 Complete.")

        logging.info("--- Discovery Run Successful ---")
        print("Video discovery executed successfully. Check collection_log.txt for details.")

    except Exception as e:
        logging.error(f"Critical error during discovery execution: {e}")
        print(f"Discovery failed. Error logged: {e}")


if __name__ == "__main__":
    run_pipeline()