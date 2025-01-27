import json
import yaml
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

# Logging function with colors and timestamps
def log(message, type="info"):
    colors = {
        "info": "\033[96m",    # Cyan
        "success": "\033[92m", # Green
        "error": "\033[91m",   # Red
        "reset": "\033[0m"
    }
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": "INFO",
        "success": "SUCCESS",
        "error": "ERROR"
    }.get(type, "INFO")
    
    sys.__stdout__.write(
        f"{colors.get(type, colors['info'])}"
        f"[{timestamp}] {prefix} {message}"
        f"{colors['reset']}\n"
    )
    sys.__stdout__.flush()

def main():
    try:
        # Load credentials from YAML file
        with open('creds.yml') as f:
            creds = yaml.safe_load(f)
            username, password = creds['username'], creds['password']
    except Exception as e:
        log("Critical: Credential load failure", type="error")
        return

    with sync_playwright() as p:
        log("Initializing browser session")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Function to handle API responses
        def handle_response(response):
            if '/api/timetable' in response.url:
                try:
                    data = response.json()
                    with open('timetable.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    log("Timetable data saved successfully!", type="success")
                except:
                    log("Failed to save timetable data", type="error")

        # Listen for network responses
        page.on('response', handle_response)
        
        # Navigate to login page
        log("Navigating to login portal")
        page.goto('https://myupes-beta.upes.ac.in/oneportal/app/auth/login')
        
        # Fill username and password
        log("Entering credentials")
        page.fill('input[name="userName"]', username)
        page.fill('input[name="password"]', password)
        
        # Click login button
        log("Attempting login")
        page.click('button[type="submit"]')
        
        try:
            # Wait for dashboard to load
            log("Validating login")
            page.wait_for_selector('.student-dashboard', timeout=10000)
            log("Login successful! Dashboard loaded.", type="success")
            
            # Navigate to timetable page
            log("Accessing timetable page")
            page.goto('https://myupes-beta.upes.ac.in/connectportal/user/student/curriculum-scheduling')
            page.wait_for_timeout(5000)  # Wait for API calls to complete
        except:
            log("Login failed or dashboard not found", type="error")
        
        browser.close()

if __name__ == '__main__':
    main()
