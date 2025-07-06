# LinkedIn Profile Scraper & AI Analyzer

This project is an automated agent that scrapes LinkedIn for profiles based on a configurable search query, analyzes their professional details using Google's Gemini LLM via Vertex AI, and saves the structured analysis into a PostgreSQL database.

## Features

- **Automated Scraping:** Uses Selenium to log in to LinkedIn, perform searches, and scrape profile data.
- **Intelligent Analysis:** Leverages LangChain and Google's Gemini Pro model to analyze scraped text and extract structured information based on a dynamic "Mission Critical Profile" (MCP).
- **Configurable & Schedulable:** The agent's mission is loaded from a PostgreSQL database, making it easy to configure and schedule via a cronjob.
- **Resilient by Design:** The main workflow processes each profile in an isolated browser session to ensure stability and prevent crashes during long runs.
- **Secure:** All credentials and sensitive files are explicitly excluded from the repository via a robust `.gitignore` file.

---

## Setup and Installation

**1. Clone the Repository:**
```bash
git clone <your-repository-url>
cd <repository-directory>
```

**2. Install Dependencies:**
It is recommended to use a Python virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Set Up PostgreSQL:**
- Ensure you have a PostgreSQL server running.
- Create a database and a user. For this project, a database named `rubeng` and a user named `rubeng` were used.
- Run the `create_tables.sql` script to set up the necessary tables (`job_schedules` and `validated_recruiters`).
```bash
psql -U rubeng -d rubeng -f create_tables.sql
```

**4. Configure Environment Variables:**
- Create a file named `.env` in the project root.
- Add your LinkedIn credentials to this file:
```
LINKEDIN_USERNAME="your-linkedin-email@example.com"
LINKEDIN_PASSWORD="your-linkedin-password"
```

**5. Set Up Google Cloud Credentials:**
- Download your Google Cloud service account key and save it in the project root as `gcp-linkedin-agent-credentials.json`.
- **Important:** The `.gitignore` file is already configured to prevent this key from being uploaded to GitHub.

**6. Download ChromeDriver:**
- This project bypasses `webdriver-manager`. You must manually download the correct version of `chromedriver` for your Chrome browser and place the executable in the project root.

---

## How to Run the Agent

Once all setup steps are complete, you can run the agent from your terminal.

The script requires the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to be set for authentication.

```bash
GOOGLE_APPLICATION_CREDENTIALS="./gcp-linkedin-agent-credentials.json" python3 run_agent.py
```

The agent will then connect to the database, retrieve its mission, and begin the scrape-analyze-save workflow.

This project implements a database-driven scheduler for LinkedIn recruiter searches.

## Setup

1. Install PostgreSQL (via Docker)
2. Create a database named `agent_db` or `myapp_db`
3. Create the `job_schedules` table
4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

- `repository.py`: Contains database interaction logic
- `requirements.txt`: Python dependencies
- `README.md`: Project documentation
