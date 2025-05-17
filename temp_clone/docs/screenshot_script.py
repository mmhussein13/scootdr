import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
BASE_URL = "http://localhost:5000"  # Replace with your application URL
SCREENSHOT_DIR = "screenshots"
USERNAME = "admin"  # Replace with your login credentials
PASSWORD = "admin"  # Replace with your login credentials

# Pages to capture
PAGES = [
    {"name": "login", "url": "/login/", "wait_for": "input[type='text']"},
    {"name": "dashboard", "url": "/", "wait_for": ".card"},
    {"name": "scooter_list", "url": "/inventory/scooter/", "wait_for": "table"},
    {"name": "parts_list", "url": "/inventory/parts/", "wait_for": "table"},
    {"name": "store_list", "url": "/inventory/store/", "wait_for": "table"},
    {"name": "stock_transfer_list", "url": "/inventory/stock-transfer/", "wait_for": "table"},
    {"name": "supplier_list", "url": "/inventory/supplier/", "wait_for": "table"},
    {"name": "purchase_list", "url": "/inventory/purchase/", "wait_for": "table"},
    {"name": "job_card_list", "url": "/service/job-card/", "wait_for": "table"},
    {"name": "customer_list", "url": "/customers/", "wait_for": "table"},
    {"name": "rental_list", "url": "/customers/rentals/", "wait_for": "table"},
    {"name": "analytics_dashboard", "url": "/analytics/", "wait_for": ".card"},
    {"name": "alerts_dashboard", "url": "/analytics/alerts/", "wait_for": ".card"},
    # Add forms
    {"name": "add_scooter", "url": "/inventory/scooter/create/", "wait_for": "form"},
    {"name": "add_part", "url": "/inventory/parts/create/", "wait_for": "form"},
    {"name": "add_store", "url": "/inventory/store/create/", "wait_for": "form"},
    {"name": "create_stock_transfer", "url": "/inventory/stock-transfer/create/", "wait_for": "form"},
    {"name": "add_supplier", "url": "/inventory/supplier/create/", "wait_for": "form"},
    {"name": "create_purchase", "url": "/inventory/purchase/create/", "wait_for": "form"},
    {"name": "create_job_card", "url": "/service/job-card/create/", "wait_for": "form"},
    {"name": "add_customer", "url": "/customers/create/", "wait_for": "form"},
    {"name": "create_rental", "url": "/customers/rentals/create/", "wait_for": "form"},
]

def setup_driver():
    """Configure and return a headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login(driver):
    """Log in to the application"""
    driver.get(f"{BASE_URL}/login/")
    
    # Wait for the login form to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    
    # Enter credentials
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    
    # Submit the form
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    # Wait for redirect to dashboard
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".sidebar"))
    )

def capture_screenshots():
    """Capture screenshots of all pages in the PAGES list"""
    driver = setup_driver()
    
    try:
        # Create screenshots directory if it doesn't exist
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        # Log in first (except for login page)
        login(driver)
        
        # Capture each page
        for page in PAGES:
            print(f"Capturing {page['name']}...")
            
            # If it's the login page, we need to log out first
            if page['name'] == 'login':
                driver.get(f"{BASE_URL}/logout/")
                time.sleep(2)  # Wait for logout to complete
                
            # Navigate to the page
            driver.get(f"{BASE_URL}{page['url']}")
            
            # Wait for the specified element to ensure page is loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, page['wait_for']))
            )
            
            # Take a screenshot
            driver.save_screenshot(f"{SCREENSHOT_DIR}/{page['name']}.png")
            print(f"✓ Captured {page['name']}")
            
            # Small pause to ensure everything is rendered
            time.sleep(1)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    print("Starting screenshot capture...")
    capture_screenshots()
    print("Screenshot capture complete!")