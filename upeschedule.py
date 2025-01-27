import yaml
from playwright.sync_api import sync_playwright

def main():
    try:
        # Load credentials from YAML file
        with open('creds.yml') as f:
            creds = yaml.safe_load(f)
            username, password = creds['username'], creds['password']
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to login page
        page.goto('https://myupes-beta.upes.ac.in/oneportal/app/auth/login')
        
        # Fill username and password
        page.fill('input[name="userName"]', username)
        page.fill('input[name="password"]', password)
        
        # Click login button
        page.click('button[type="submit"]')
        
        try:
            # Wait for dashboard to load
            page.wait_for_selector('.student-dashboard', timeout=10000)
            print("Login successful! Dashboard loaded.")
        except:
            print("Login failed or dashboard not found.")
        
        browser.close()

if __name__ == '__main__':
    main()
