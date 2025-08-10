# linkedin_agent/linkedin_module.py

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus

def setup_driver():
    """Sets up a robust Chrome driver using a manually specified path from an environment variable."""
    print("--- Setting up Chrome driver from manual path ---")
    
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
    if not chromedriver_path or not os.path.exists(chromedriver_path):
        raise ValueError(
            "CHROMEDRIVER_PATH environment variable is not set or points to a non-existent file. "
            "Please set it to the absolute path of your chromedriver executable."
        )

    print(f"Using chromedriver from: {chromedriver_path}")
    
    options = webdriver.ChromeOptions()
    
    # El navegador será VISIBLE para que puedas resolver cualquier CAPTCHA.
    # options.add_argument('--headless') 
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--start-maximized')
    
    service = ChromeService(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    driver.set_page_load_timeout(30)
    return driver

def _login_to_linkedin(driver, username, password):
    """Logs into LinkedIn."""
    print("--- Attempting to log in to LinkedIn ---")
    try:
        driver.get("https://www.linkedin.com/login")
        
        # Espera a que los campos de usuario y contraseña estén presentes
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        
        # Introduce las credenciales
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        
        # Haz clic en el botón de inicio de sesión
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Espera a que la página de inicio cargue (un indicador es el icono de 'Mi Red')
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
        )
        print("--- Login successful! ---")
        return True
    except TimeoutException:
        print("CRITICAL: Login failed. Either credentials are wrong or a security check (CAPTCHA) is required.")
        print("The browser window is open. Please check for any security challenges and solve them manually.")
        # Mantén el navegador abierto por un tiempo para que el usuario pueda intervenir
        time.sleep(60) 
        return False
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return False

def search_for_people(driver, query, location="Worldwide"):
    """Performs a search for people on LinkedIn."""
    print(f"--- Searching for '{query}' in '{location}' ---")
    encoded_query = quote_plus(query)
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
    driver.get(search_url)
    # Estrategia robusta: esperar a que el cuerpo de la página cargue y luego pausar.
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(3) # Pausa extra para que el contenido dinámico cargue.

def extract_urls_from_current_page(driver):
    """Extracts all profile URLs from the current search results page."""
    urls = []
    try:
        # Estrategia robusta: buscar enlaces de perfil dentro de cualquier elemento de lista (li).
        search_results = driver.find_elements(By.XPATH, "//li//a[contains(@href, '/in/')]")
        for result in search_results:
            url = result.get_attribute('href').split('?')[0]
            if "/in/" in url and "/company/" not in url and "/school/" not in url and url not in urls:
                urls.append(url)
    except Exception as e:
        print(f"An error occurred while extracting URLs: {e}")
    print(f"Found {len(urls)} profile URLs on the current page.")
    return urls

def click_next_page(driver):
    """Clicks the 'Next' button to go to the next page of search results."""
    try:
        # LinkedIn carga la paginación dinámicamente, así que primero hacemos scroll.
        print("Scrolling to bottom of page to load pagination...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2) # Espera a que aparezca el botón

        # Selector flexible para encontrar el botón 'Siguiente' en español o 'Next' en inglés.
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Siguiente') or contains(@aria-label, 'Next')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)
        next_button.click()
        time.sleep(2)
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
        # Estrategia robusta: esperar a que el cuerpo de la página cargue.
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        # Extrae todo el texto visible del perfil
        profile_text = driver.find_element(By.TAG_NAME, "body").text
        return profile_text
    except Exception as e:
        print(f"Could not scrape profile {profile_url}. Reason: {e}")
        return None