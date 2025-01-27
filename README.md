# upeschedule

Fetches your UPES timetable automatically using GitHub Actions. Logs in, grabs the schedule, and updates a Gist every 6 hours.

## How it works:
1. **GitHub Action**: Runs the script every 6 hours (or manually).
2. **Tools Used**:
   - **Playwright**: Automates browser actions (login, navigation).
   - **PyYAML**: Handles credentials from a YAML file.
   - **GitHub Gist**: Stores the updated timetable for easy access.

## Steps:
- Logs into UPES portal.
- Fetches timetable data.
- Updates a GitHub Gist with the latest schedule.
