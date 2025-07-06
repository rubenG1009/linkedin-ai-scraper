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
    """Sets up and returns a Selenium WebDriver instance."""
    print("Setting up Chrome driver...")
    # This uses the local chromedriver you downloaded
    service = webdriver.chrome.service.Service(executable_path="./chromedriver")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    return driver

def _login_to_linkedin(driver, username, password):
    """(Private) Logs into LinkedIn."""
    print("Navigating to LinkedIn login page...")
    driver.get('https://www.linkedin.com/login')
    
    print("Page loaded. Pausing for 15 seconds for manual CAPTCHA...", flush=True)
    time.sleep(15)
    print("Pause finished. Attempting to log in...")

    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.send_keys(username)
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
        )
        print("Login successful!", flush=True)
        return True
    except Exception as e:
        print(f"An error occurred during login: {e}", flush=True)
        driver.save_screenshot('linkedin_login_error.png')
        return False

def perform_search_and_get_urls(driver, search_query):
    """
    Logs in, performs a search, scrolls to load all results, and returns profile URLs.
    """
    if not _login_to_linkedin(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
        print("Login failed. Aborting search.")
        return []

    print(f"\nSearching for people with query: '{search_query}'")
    try:
        encoded_query = quote_plus(search_query)
        people_search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
        driver.get(people_search_url)
        WebDriverWait(driver, 15).until(EC.url_contains("/people/"))
        print("Successfully loaded 'People' filtered search results.")
    except Exception as e:
        print(f"Could not navigate to search results page: {e}")
        return []

    print("Scrolling to load all search results...")
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(10): # Limit scrolls to prevent infinite loops
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("Finished scrolling.")
    except Exception as e:
        print(f"An error occurred during scrolling: {e}")

    print("Extracting profile URLs...")
    profile_urls = []
    try:
        # Wait for a more stable, general container for the search results.
        search_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-results-container')]"))
        )

        # Find all list items within the container, ignoring specific, volatile class names.
        profile_elements = search_container.find_elements(By.XPATH, ".//li")

        if not profile_elements:
            print("Found search container, but no profile list items ('li') were inside. Saving screenshot.")
            driver.save_screenshot('linkedin_extraction_error.png')
            return []

        for elem in profile_elements:
            try:
                # Find the link to the profile within the list item.
                link_tag = elem.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                url = link_tag.get_attribute('href').split('?')[0]
                if url not in profile_urls:
                    profile_urls.append(url)
            except NoSuchElementException:
                # It's normal for some 'li' elements to not be profiles (e.g., ads), so we just skip them.
                continue

        print(f"Extracted {len(profile_urls)} unique profile URLs.")
        return profile_urls

    except TimeoutException:
        print("Could not find the main search results container. The page structure has likely changed. Saving screenshot.")
        driver.save_screenshot('linkedin_extraction_error.png')
        return []
    except Exception as e:
        print(f"An unexpected error occurred during URL extraction: {e}")
        driver.save_screenshot('linkedin_extraction_error.png')
        return []

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
