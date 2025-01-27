from playwright.sync_api import sync_playwright

def main():
    TEST_CREDS = {
        "username": "kushagra",
        "password": "secret"
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
        
        browser.close()

if __name__ == '__main__':
    main()
