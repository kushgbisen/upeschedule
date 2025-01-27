from playwright.sync_api import sync_playwright

def main():
    TEST_CREDS = {
        "username": "test_user",
        "password": "test_pass"
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to login page
        page.goto('https://myupes-beta.upes.ac.in/oneportal/app/auth/login')
        
        # Fill username and password
        page.fill('input[name="userName"]', TEST_CREDS["username"])
        page.fill('input[name="password"]', TEST_CREDS["password"])
        
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
