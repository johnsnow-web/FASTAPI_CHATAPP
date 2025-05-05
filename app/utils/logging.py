import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_performance(action, start_time, end_time):
    """Logs execution time for an action."""
    duration = end_time - start_time
    logging.info(f"{action} completed in {duration:.2f} seconds.")
