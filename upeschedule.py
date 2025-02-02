import json
import os
import shutil
import sys

import re
from datetime import datetime
from contextlib import suppress
from playwright.sync_api import sync_playwright



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

        "info": "[i]",         # Info symbol
        "success": "[✓]",      # Success symbol
        "error": "[✗]"         # Error symbol
    }.get(type, "[i]")
    
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

def normalize_text(text):
    """Removes extra spaces and normalizes text."""
    return " ".join(text.split()) if isinstance(text, str) else text


def remove_modulecode_suffix(module_code):
    """Removes _N suffix from module code."""
    if isinstance(module_code, str):
        return re.sub(r'_\d+$', '', module_code)
    return module_code


def remove_coursefamilycode_suffix(course_family_code):
    """Removes _ suffix from course family code."""
    if isinstance(course_family_code, str):
        return re.sub(r'_$', '', course_family_code)
    return course_family_code

def remove_cohortcode_suffix(cohort_code):
    """Removes _ and any suffix from cohort code."""
    if isinstance(cohort_code, str):
        return re.sub(r'_.*$', '', cohort_code)
    return cohort_code

def remove_whitespace_before_parenthesis(text):
    """Removes whitespace before parentheses in text."""

    if isinstance(text, str):
        return re.sub(r'\s+\(', '(', text)
    return text

def extract_batch_from_cohort_code(cohort_code):
    """Extracts the batch identifier (e.g., B1, B2) from the cohort code."""
    if not isinstance(cohort_code, str):
        return None
    parts = cohort_code.split('-')
    return parts[-1].strip() if parts else None

def parse_time(time_str):
    """Converts time string to total minutes since midnight."""
    try:
        time_obj = datetime.strptime(time_str, '%I:%M %p')
        return time_obj.hour * 60 + time_obj.minute
    except (ValueError, TypeError):
        log(f"Warning: Invalid time format: {time_str}", type="error")
        return None

def determine_class_type(start_time, end_time, module_code, cohort_list):
    """Determines class type based on duration and module."""
    start_minutes = parse_time(start_time)
    end_minutes = parse_time(end_time)


    if None in (start_minutes, end_minutes) or not cohort_list or not module_code:
        return None
    duration = end_minutes - start_minutes
    if duration > 55:
        return "LAB"
    elif module_code.startswith("MATH1066") and len(cohort_list) == 1:
        return "Tutorial"
    elif module_code == "CSEG1021":
        return "Lecture"
    else:
        return "Theory"

def clean_timetable_data(data):
    """Cleans and normalizes timetable JSON data."""

    for item in data:
        # Normalize text fields
        if 'FloorPlanDetails' in item and item['FloorPlanDetails']:
            details = item['FloorPlanDetails']
            if 'VenueName' in details:
                details['VenueName'] = normalize_text(details['VenueName'])

        if 'TeacherList' in item:
            for teacher in item['TeacherList']:
                if 'Name' in teacher:

                    teacher['Name'] = normalize_text(teacher['Name'])


        if 'ContextCombination' in item and item['ContextCombination']:
            for context in item['ContextCombination']:
                if 'CourseFamilyCode' in context:
                    context['CourseFamilyCode'] = remove_coursefamilycode_suffix(context['CourseFamilyCode'])


        if 'ModuleList' in item:
            for module in item['ModuleList']:
                if 'ModuleCode' in module:
                    module['ModuleCode'] = remove_modulecode_suffix(module['ModuleCode'])
                if 'ModuleName' in module:
                    module['ModuleName'] = remove_whitespace_before_parenthesis(normalize_text(module['ModuleName']))

        if 'CohortList' in item:
            for cohort in item['CohortList']:
                if 'Code' in cohort:
                    cohort['Code'] = remove_cohortcode_suffix(cohort['Code'])
                if 'Name' in cohort:
                    cohort['Name'] = remove_whitespace_before_parenthesis(normalize_text(cohort['Name']))

        # Add ClassType
        if "SlotStartTime" in item and "SlotEndTime" in item and "ModuleList" in item and item["ModuleList"] and "CohortList" in item:
            module_code = item['ModuleList'][0].get('ModuleCode', '')
            cohort_list = item.get('CohortList', [])
            class_type = determine_class_type(
                item['SlotStartTime'],

                item['SlotEndTime'],
                module_code,
                cohort_list
            )
            if class_type:
                item['ClassType'] = class_type


        # Add Batch
        all_batches = []
        if "CohortList" in item and item["CohortList"]:
            for cohort in item["CohortList"]:
                batch = extract_batch_from_cohort_code(cohort.get('Code', ''))
                if batch:
                    all_batches.append(batch)
        unique_batches = list(set(all_batches)) if all_batches else None
        item['Batch'] = unique_batches if unique_batches else None

        # Add timestamp
        item['LastUpdated'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return data

def main():
    # Pre-flight cleanup
    with suppress(Exception):
        shutil.rmtree('user_data', ignore_errors=True)
        os.remove('timetable.json')

    # Load credentials from environment variables
    try:
        username = os.environ.get('UPES_USERNAME')
        password = os.environ.get('UPES_PASSWORD')
        
        if not username or not password:

            log("Critical: Empty credentials in environment variables", type="error")
            return
            
    except Exception as e:
        log(f"Critical: Environment variables not set - {str(e)}", type="error")
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
                        cleaned_data = clean_timetable_data(data)
                        with open('timetable.json', 'w') as f:
                            json.dump(cleaned_data, f, indent=2)
                        log("Timetable data secured and cleaned", type="success")
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
