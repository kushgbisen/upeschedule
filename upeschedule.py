import json
import yaml
import os
import shutil
import sys
from contextlib import suppress

from playwright.sync_api import sync_playwright
from datetime import datetime

# Enhanced logging with different modes
def log(message, type="info"):
    colors = {
        "info": "\033[96m",    # Cyan
        "success": "\033[92m", # Green
        "error": "\033[91m",   # Red

        "reset": "\033[0m"     # Reset

    }
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": "➤",
        "success": "✔",
        "error": "✘"
    }.get(type, "➤")
    
    sys.__stdout__.write(
        f"{colors.get(type, colors['info'])}"

        f"[{timestamp}] {prefix} {message}"
        f"{colors['reset']}\n"
    )
    sys.__stdout__.flush()

def is_valid_json(response):
    """Check if the JSON response is valid and has more than 10,000 lines."""
    try:
        data = response.json()

        json_str = json.dumps(data, indent=2)
        lines = json_str.splitlines()
        return len(lines) > 10000  # Ensure JSON is approximately 20,000 lines

    except:
        return False

def main():
    # Pre-flight cleanup

    with suppress(Exception):
        shutil.rmtree('user_data', ignore_errors=True)
        os.remove('timetable.json')

    # Load credentials

    if not os.path.exists('creds.yml'):
        log("Critical: creds.yml file not found", type="error")
        return


    try:
        with open('creds.yml') as f:
            creds = yaml.safe_load(f)
            username, password = creds['username'], creds['password']
    except Exception as e:
        log(f"Critical: Credential load failure - {str(e)}", type="error")
        return

    with suppress(Exception), sync_playwright() as p:

        log("Initializing secure browser session")
        browser = p.chromium.launch_persistent_context(
            user_data_dir='./user_data',
            headless=True,
            viewport={'width': 1366, 'height': 768}
        )
        page = browser.new_page()

        def handle_response(response):
            if '/api/timetable' in response.url:
                if is_valid_json(response):

                    try:
                        data = response.json()
                        with open('timetable.json', 'w') as f:
                            json.dump(data, f, indent=2)

                        log("Timetable data secured", type="success")
                        sys.exit(0)
                    except Exception as e:
                        log(f"Error processing response: {str(e)}", type="error")

        page.on('response', handle_response)

        try:
            log("Authenticating to university portal")
            page.goto('https://myupes-beta.upes.ac.in/oneportal/app/auth/login', timeout=10000)
            page.fill('input[name="userName"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')


            log("Validating credentials")
            page.wait_for_url('**/connectportal/**', timeout=10000)

            log("Accessing curriculum schedule")
            page.goto('https://myupes-beta.upes.ac.in/connectportal/user/student/curriculum-scheduling', timeout=15000)

            log("Monitoring network requests")
            retries = 5  # Number of retries to find a valid JSON
            while retries > 0:

                page.wait_for_timeout(5000)  # Wait for responses
                log(f"Retrying... Attempts left: {retries}", type="info")
                retries -= 1


            log("Failed to retrieve valid timetable data", type="error")


        except Exception as e:
            log(f"Connection timeout occurred: {str(e)}", type="error")

if __name__ == '__main__':
    # Suppress all default output

    with open(os.devnull, 'w') as f:
        sys.stdout = f
        sys.stderr = f
        main()

    # Silent cleanup
    with suppress(Exception):
        shutil.rmtree('user_data', ignore_errors=True)
