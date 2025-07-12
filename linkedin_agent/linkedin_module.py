# linkedin_module.py - A refactored, importable module for Selenium tasks

import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus

# Load credentials from .env file
load_dotenv()
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

def setup_driver():
    """Sets up a robust Chrome driver for Selenium with stability options."""
    print("Setting up Chrome driver...")
    # This uses the local chromedriver you downloaded
    service = webdriver.chrome.service.Service(executable_path="./chromedriver")
    options = webdriver.ChromeOptions()
    # --- Stability Options ---
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--start-maximized')
    # Optional: To run headless (without a visible browser window)
    options.add_argument('--headless')
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    # Add a page load timeout to prevent indefinite hangs
    driver.set_page_load_timeout(30)
    return driver

def _login_to_linkedin(driver, username, password):
    """(Private) Logs into LinkedIn with robust retry logic for navigation."""
    login_url = 'https://www.linkedin.com/login'
    
    # --- Navigation with Retry Logic ---
    navigation_successful = False
    for attempt in range(3):
        try:
            print(f"Navigating to LinkedIn login page (Attempt {attempt + 1}/3)...")
            driver.get(login_url)
            
            # Explicitly wait for a key element (the username field) to be present after navigation
            print("DEBUG: Page navigation initiated. Waiting for page to be fully loaded...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            print("DEBUG: Page loaded and key element is present.")
            navigation_successful = True
            break # If successful, exit the loop
            
        except TimeoutException:
            print(f"Timeout loading login page on attempt {attempt + 1}. Retrying...")
        except Exception as e:
            print(f"An unexpected error occurred during navigation on attempt {attempt + 1}: {e}")

    if not navigation_successful:
        print("Failed to load login page after multiple attempts. Aborting login.")
        return False

    # --- Login Credentials Input ---
    print("Page loaded and ready. Attempting to log in immediately...")
    try:
        # Use atomic JavaScript calls to find and interact with elements in a single step.
        driver.execute_script("document.getElementById('username').value = arguments[0];", username)
        driver.execute_script("document.getElementById('password').value = arguments[0];", password)
        driver.execute_script("document.querySelector('button[type=\"submit\"]').click();")

        # Wait for a known element on the home page to confirm login
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
        )
        print("Login successful!", flush=True)
        return True
    except Exception as e:
        print(f"An error occurred during login: {e}", flush=True)
        driver.save_screenshot('linkedin_login_error.png')
        return False

def search_for_people(driver, search_query):
    """Navigates to the search results page for a given query."""
    print(f"\nSearching for people with query: '{search_query}'")
    try:
        encoded_query = quote_plus(search_query)
        people_search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
        driver.get(people_search_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-results-container')]")))
        print("Successfully loaded 'People' filtered search results.")
        return True
    except Exception as e:
        print(f"Could not navigate to search results page: {e}")
        return False

def extract_urls_from_current_page(driver):
    """Extracts all unique profile URLs from the currently visible search results page."""
    print("Extracting profile URLs from current page...")
    try:
        # Scroll once to ensure all elements on the page are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # The outer container for search results.
        search_container = driver.find_element(By.XPATH, "//div[contains(@class, 'search-results-container')]")
        # Find all list items directly within that container. This is more general and robust.
        profile_elements = search_container.find_elements(By.XPATH, ".//li")
        
        urls = []
        for elem in profile_elements:
            try:
                link_tag = elem.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                url = link_tag.get_attribute('href').split('?')[0]
                if url not in urls:
                    urls.append(url)
            except NoSuchElementException:
                continue
        
        print(f"Extracted {len(urls)} unique profile URLs from this page.")
        return urls
    except Exception as e:
        print(f"An unexpected error occurred during URL extraction: {e}")
        driver.save_screenshot('linkedin_extraction_error.png')
        return []

def click_next_page(driver):
    """Clicks the 'Next' button on the search results page and returns False if it's the last page."""
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next']"))
        )
        # Scroll to the button to ensure it's in view before clicking
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)
        next_button.click()
        time.sleep(2)  # Wait for the next page to load
        return True
    except (TimeoutException, NoSuchElementException):
        print("INFO: 'Next' button not found. Reached the last page of results.")
        return False
    except Exception as e:
        print(f"An error occurred while trying to click 'Next': {e}")
        return False

def scrape_full_profile_details(driver, profile_url):
    """Navigates to a profile URL and scrapes its text content."""
    print(f"Scraping details from: {profile_url}")
    try:
        driver.get(profile_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//h1")))
        time.sleep(2)

        name = driver.find_element(By.XPATH, "//h1").text
        headline = driver.find_element(By.XPATH, "//div[contains(@class, 'text-body-medium')]").text
        
        about_text = ""
        try:
            about_section = driver.find_element(By.XPATH, "//section[.//h2[contains(text(), 'About')]]")
            about_text = about_section.text
        except NoSuchElementException:
            pass

        experience_text = ""
        try:
            experience_section = driver.find_element(By.ID, "experience")
            experience_text = experience_section.text
        except NoSuchElementException:
            pass

        full_details = f"Name: {name}\nHeadline: {headline}\n\n{about_text}\n\n{experience_text}"
        return full_details.strip()

    except Exception as e:
        print(f"Error scraping details for {profile_url}: {e}")
        return None
