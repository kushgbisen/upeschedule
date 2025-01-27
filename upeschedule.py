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
        "reset": "\033[0m"
    }
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": "➤",
        "success": "✔"
    }.get(type, "➤")
    
    sys.__stdout__.write(
        f"{colors.get(type, colors['info'])}"
        f"[{timestamp}] {prefix} {message}"
        f"{colors['reset']}\n"
    )
    sys.__stdout__.flush()

def main():
    # Pre-flight cleanup
    with suppress(Exception):
        shutil.rmtree('user_data', ignore_errors=True)
        os.remove('timetable.json')

    try:
        with open('creds.yml') as f:
            creds = yaml.safe_load(f)
            username, password = creds['username'], creds['password']
    except Exception as e:
        log("Critical: Credential load failure", type="error")
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
                try:
                    data = response.json()
                    if "UPES_BID" in json.dumps(data):
                        with open('timetable.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        log("Timetable data secured", type="success")
                        os._exit(0)
                except:
                    pass

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
            page.wait_for_timeout(5000)

        except Exception as e:
            log("Connection timeout occurred", type="error")

if __name__ == '__main__':
    # Suppress all default output
    with open(os.devnull, 'w') as f:
        sys.stdout = f
        sys.stderr = f
        main()
    
    # Silent cleanup
    with suppress(Exception):
        shutil.rmtree('user_data', ignore_errors=True)