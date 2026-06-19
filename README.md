# Cyber Fraud Reporting Bot

A secure and automated Telegram Bot designed to help citizens report cyber fraud incidents directly to the cyber cell. The backend is built using Python and integrates with Google Sheets via a Google Apps Script Web API to store reports, track duplicate submissions, and compute risk levels.

## System Architecture

The application operates as a distributed system:
1. **User Interface:** Users interact with the Telegram bot client.
2. **Backend Application:** A Python server processes user inputs, performs format validations, and coordinates communications.
3. **Database & Storage Layer:** Google Sheets serves as the database for report storage, accessed via a custom Google Apps Script endpoint. Screenshots are uploaded directly to Google Drive.

## Key Features

* **Incident Reporting:** Guides users step-by-step to report various cyber fraud types, including UPI fraud, OTP fraud, loan scams, job scams, investment scams, and malicious websites.
* **Input Validation:** Automatically validates formats for inputs like UPI IDs and website URLs before acceptance.
* **Duplicate Detection:** Scans the repository of reports to count duplicate reports against specific identifiers (e.g., the same UPI ID or website).
* **Risk Scoring:** Assigns risk thresholds (Low, Medium, High, Critical) automatically based on the frequency of reports matching a specific identifier.
* **Evidence Management:** Supports screenshot uploads, storing them in Google Drive and linking them directly within the reporting database.
* **Status Querying:** Allows citizens to check the real-time status of their investigation using a unique Report ID.
* **Awareness Resources:** Provides safety tips and emergency contact information within the bot menu.

## Project Structure

* `bot.py` - The entry point that registers handlers and initiates the Telegram polling service.
* `config.py` - Manages application settings and environment variables.
* `handlers/` - Modules handling different conversation stages:
  * `start.py` - Menu interface and startup commands.
  * `report.py` - Multi-step reporting wizard.
  * `status.py` - Report status retrieval flow.
  * `awareness.py` - Safety education content.
* `services/` - External integrations:
  * `sheets.py` - Handles API requests to the Google Apps Script endpoint.
  * `validator.py` - Text and format validation utility.
* `utils/` - Utility functions:
  * `report_id.py` - Generates unique case identifiers.
* `requirements.txt` - Python package dependencies.
* `google_apps_script/` (Excluded from VCS) - Google Apps Script deployment code (`Code.gs`).

## Installation and Setup

### Prerequisites

* Python 3.10 or higher
* A Telegram Bot token obtained from `@BotFather`
* A deployed Google Apps Script web application (using the provided script template)

### Configuration

Create a `.env` file in the root directory of the project. This file is excluded from version control for security. Add the following parameters:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
APPS_SCRIPT_URL=https://script.google.com/macros/s/your_script_id_here/exec
```

### Running the Application

1. Clone the repository to your local environment.
2. Ensure you have the dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python bot.py
   ```
   Note: The entry point is configured to auto-verify and install missing packages listed in `requirements.txt` upon startup.