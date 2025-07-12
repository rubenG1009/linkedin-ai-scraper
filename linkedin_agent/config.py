# linkedin_agent/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file located in the project root
# We construct the path to the .env file relative to this config file.
# This makes it robust, regardless of where the script is called from.
_PROYECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_PROYECT_ROOT, '.env')

if os.path.exists(_ENV_PATH):
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    # This will be handled more gracefully by the 'configure' command later
    print("Warning: .env file not found. Please create one.")

# --- LinkedIn Credentials ---
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# --- Database Configuration ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
# Password is often not needed for local connections with 'trust' authentication
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# --- Validation Function ---
def get_checked_config():
    """Checks if essential credentials are provided and returns them."""
    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        raise ValueError("LinkedIn credentials (LINKEDIN_USERNAME, LINKEDIN_PASSWORD) are not set in the .env file.")
    if not DB_USER or not DB_NAME:
        raise ValueError("Database credentials (DB_USER, DB_NAME) are not set in the .env file.")
    
    print("DEBUG: Configuration loaded and validated successfully.")
    return {
        "linkedin_username": LINKEDIN_USERNAME,
        "linkedin_password": LINKEDIN_PASSWORD,
        "db_host": DB_HOST,
        "db_user": DB_USER,
        "db_name": DB_NAME,
        "db_password": DB_PASSWORD
    }
