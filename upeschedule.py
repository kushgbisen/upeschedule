import json
import yaml
import os
import shutil
from playwright.sync_api import sync_playwright

def main():
    # Cleanup
    shutil.rmtree('user_data', ignore_errors=True)
    if os.path.exists('timetable.json'):
        os.remove('timetable.json')

    # Load credentials
    with open('creds.yml') as f:
        username, password = yaml.safe_load(f).values()

    # Browser automation
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir='./user_data', headless=True
        )
        page = browser.new_page()

        # Save timetable data
        def save_timetable(response):
            if '/api/timetable' in response.url:
                with open('timetable.json', 'w') as f:
                    json.dump(response.json(), f, indent=2)
                print("Timetable saved successfully!")
                os._exit(0)

        page.on('response', save_timetable)

        # Login
        page.goto('https://myupes-beta.upes.ac.in/oneportal/app/auth/login')
        page.fill('input[name="userName"]', username)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')

        # Navigate to timetable
        page.wait_for_url('**/connectportal/**')
        page.goto('https://myupes-beta.upes.ac.in/connectportal/user/student/curriculum-scheduling')
        page.wait_for_timeout(5000)

        browser.close()

if __name__ == '__main__':
    main()
