import os
import time
from urllib.parse import quote_plus
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import sqlite3  # Example, change if you use a different database like PostgreSQL or MySQL

# =============================================================================
# 1. LOGIN FUNCTION
# =============================================================================
def login_to_linkedin(driver, username, password):
    """
    Navigates to LinkedIn, handles CAPTCHA pause, and logs in.
    """
    print("Navigating to LinkedIn login page...", flush=True)
    driver.get('https://www.linkedin.com/login')
    
    print("Page loaded. Pausing for 15 seconds for manual CAPTCHA...", flush=True)
    time.sleep(15)
    print("Pause finished. Attempting to log in...", flush=True)

    try:
        print("Attempting to find username field...", flush=True)
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.send_keys(username)

        print("Attempting to find password field...", flush=True)
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)

        print("Attempting to click login button...", flush=True)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        print("Waiting for login to complete...", flush=True)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
        )
        print("Login successful!", flush=True)
        return True

    except Exception as e:
        print(f"An error occurred during login: {e}", flush=True)
        driver.save_screenshot('linkedin_login_error.png')
        return False

# =============================================================================
# 2. FILTER FUNCTION
# =============================================================================
def filter_search_results_to_people(driver, search_query):
    """
    Navigates directly to the 'People' filtered search results URL.
    """
    print("\nFiltering by 'People' by navigating directly to the URL...", flush=True)
    try:
        encoded_query = quote_plus(search_query)
        people_search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
        driver.get(people_search_url)
        WebDriverWait(driver, 15).until(EC.url_contains("/people/"))
        print("Successfully loaded 'People' filtered search results.", flush=True)
        return True
    except Exception as e:
        print(f"Error filtering results: {e}", flush=True)
        driver.save_screenshot('linkedin_filter_error.png')
        return False

# =============================================================================
# 3. EXTRACTION FUNCTION
# =============================================================================
def extract_profile_links_from_search_results(driver):
    """
    Scrolls the page to load all results and extracts profile URLs and names.
    """
    print("\n--- Starting Profile Extraction ---", flush=True)
    profiles = set()
    try:
        print("Scrolling to load all results...", flush=True)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        print("Scrolling complete. Extracting profile links...", flush=True)
        # NEW, MORE ROBUST SELECTOR based on role attribute:
        # Find all list items (li) within an unordered list (ul) that has role='list'.
        profile_elements = driver.find_elements(By.XPATH, "//ul[@role='list']/li")
        print(f"Found {len(profile_elements)} potential profile elements.", flush=True)

        for element in profile_elements:
            try:
                # Within each list item, find the main profile link.
                # This link is an 'a' tag that contains the person's name in a specific span.
                link_element = element.find_element(By.XPATH, ".//a[contains(@href, '/in/') and .//span[@aria-hidden='true']]")
                profile_url = link_element.get_attribute('href').split('?')[0]
                
                # The name is inside a span within that same link.
                name_element = link_element.find_element(By.XPATH, ".//span[@aria-hidden='true']")
                profile_name = name_element.text.strip()

                if profile_url and profile_name:
                    profiles.add((profile_url, profile_name))
            except NoSuchElementException:
                # This handles cases where a list item might not be a profile (e.g., an ad).
                continue
        return list(profiles)
    except Exception as e:
        print(f"An error occurred during profile extraction: {e}", flush=True)
        driver.save_screenshot('linkedin_extraction_error.png')
        return []

# =============================================================================
# 4. SAVE TO CSV FUNCTION
# =============================================================================
# =============================================================================
# 5. SAVE TO DATABASE FUNCTION (PLACEHOLDER)
# =============================================================================
def save_profiles_to_database(profiles, db_name="linkedin_data.db"):
    """Saves the extracted profiles to a database. THIS IS A TEMPLATE."""
    print(f"\nAttempting to save {len(profiles)} profiles to database...", flush=True)
    print("NOTE: This is a placeholder function. You need to add your database logic.", flush=True)
    
    # 1. --- YOUR DATABASE CONNECTION CODE HERE ---
    # Replace this with your actual database connection from repository.py
    # Example for SQLite:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 2. --- YOUR TABLE CREATION CODE HERE (Optional) ---
    # Make sure a table exists. You can run your create_tables.sql or do it here.
    # Example for SQLite:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE
        )
    ''')

    # 3. --- YOUR INSERTION LOGIC HERE ---
    profiles_added = 0
    for url, name in profiles:
        try:
            # Example for SQLite: Use INSERT OR IGNORE to avoid duplicates on the UNIQUE url column
            cursor.execute("INSERT OR IGNORE INTO profiles (name, url) VALUES (?, ?)", (name, url))
            if cursor.rowcount > 0:
                profiles_added += 1
        except Exception as e:
            print(f"Could not insert profile {name}: {e}", flush=True)

    # 4. --- YOUR COMMIT AND CLOSE LOGIC HERE ---
    # Example for SQLite:
    conn.commit()
    conn.close()
    
    print(f"Database operation complete. Added {profiles_added} new profiles.", flush=True)


# =============================================================================
# 4. SAVE TO CSV FUNCTION
# =============================================================================
def save_profiles_to_csv(profiles, filename="linkedin_profiles.csv"):
    """Saves the extracted profiles to a CSV file."""
    print(f"\nSaving {len(profiles)} profiles to {filename}...", flush=True)
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Name', 'URL'])  # Write header
            # The profiles are tuples of (URL, Name), so we write them out.
            for url, name in profiles:
                writer.writerow([name, url])
        print(f"Successfully saved profiles to {filename}", flush=True)
    except Exception as e:
        print(f"Error saving to CSV: {e}", flush=True)


# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================
if __name__ == "__main__":
    print("--- Starting LinkedIn Automation Script ---", flush=True)

    if not os.path.exists('.env'):
        print("Error: .env file not found!", flush=True)
        exit()

    load_dotenv()
    LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        print("Error: Credentials not found in .env file.", flush=True)
        exit()

    SEARCH_QUERY = "Technical Recruiter Python"
    driver = None
    try:
        print("Setting up Chrome driver...", flush=True)
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')

        # Pointing to the local chromedriver
        chromedriver_path = os.path.join(os.getcwd(), 'chromedriver')
        if not os.path.exists(chromedriver_path):
            print(f"Error: chromedriver not found at {chromedriver_path}")
            print("Please download the correct version and place it in the project folder.")
            exit()
            
        service = Service(executable_path=chromedriver_path)
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

        if login_to_linkedin(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
            if filter_search_results_to_people(driver, SEARCH_QUERY):
                time.sleep(3) # Pause to ensure page is fully loaded
                profiles = extract_profile_links_from_search_results(driver)
                if profiles:
                    # Sort profiles by name for consistent output
                    sorted_profiles = sorted(profiles, key=lambda x: x[1])
                    print("\n--- Extracted Profiles ---", flush=True)
                    for url, name in sorted_profiles:
                        print(f"Name: {name}, Profile: {url}", flush=True)
                    # Save the sorted profiles to a CSV file
                    save_profiles_to_csv(sorted_profiles)
                    # Attempt to save to the database using the placeholder function
                    save_profiles_to_database(sorted_profiles)
                else:
                    print("Could not extract any profiles.", flush=True)
        else:
            print("Login failed. Cannot proceed.", flush=True)

    except Exception as e:
        print(f"An unexpected error occurred in the main block: {e}", flush=True)
        if driver:
            driver.save_screenshot('main_script_error.png')
    finally:
        if driver:
            input("\nScript finished. Press Enter to close the browser...")
            driver.quit()
        print("--- Script Finished ---", flush=True)
