# 🤖 LinkedIn AI-Powered Recruitment Agent

This project is an automated agent that scrapes LinkedIn for candidate profiles based on a search query, uses Google's Vertex AI to analyze their suitability for a role, and saves the results to a PostgreSQL database.

## ✨ Key Features

- **Automated LinkedIn Scraping**: Navigates LinkedIn, performs searches, and extracts profile data robustly.
- **AI-Powered Analysis**: Leverages LangChain and Google Vertex AI to analyze profile text and score candidates against job requirements.
- **CLI Interface**: Easy-to-use command-line interface to run the agent with custom queries.
- **Database Storage**: Stores scraped data and AI analysis in a PostgreSQL database for persistence and further analysis.
- **Robust & Resilient**: Built with error handling and modern web scraping techniques to handle dynamic web content.

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **PostgreSQL**: A running instance of PostgreSQL.
- **Google Cloud SDK**: Required for AI analysis.
- **Homebrew** (for macOS users): The easiest way to install dependencies.

### 1. Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **(macOS) Install Google Cloud SDK:**
    ```bash
    brew install --cask google-cloud-sdk
    ```

4.  **Authenticate with Google Cloud:**
    This will open a browser window for you to log in.
    ```bash
    gcloud auth application-default login
    ```

### 2. Configuration

1.  **Create a `.env` file** from the example:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** with your credentials:
    - `LINKEDIN_USERNAME`: Your LinkedIn email.
    - `LINKEDIN_PASSWORD`: Your LinkedIn password.
    - `CHROMEDRIVER_PATH`: The absolute path to your `chromedriver` executable.
    - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`: Your PostgreSQL connection details.

3.  **Set up the database schema** by running the SQL script located in the `database/` folder:
    ```sql
    -- Connect to your PostgreSQL instance and run the content of:
    -- database/create_tables.sql
    ```

### 3. Usage

Run the agent from the command line with a search query. The `--location` argument is optional.

```bash
python -m linkedin_agent.cli run --query "Python Developer" --location "Remote"
```

The agent will start, log in to LinkedIn, perform the search, scrape profiles, analyze them, and save the results to your database.

## 📂 Project Structure

```
.
├── .env.example          # Example environment variables
├── .gitignore            # Files to be ignored by Git
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── setup.py              # Project setup for packaging
├── database/
│   └── create_tables.sql # SQL script for database schema
└── linkedin_agent/
    ├── __init__.py
    ├── cli.py            # Command-line interface logic (argparse)
    ├── langchain_module.py # AI analysis functions
    ├── linkedin_module.py  # Selenium-based scraping functions
    ├── repository.py     # Database interaction functions
    └── run_agent.py      # Main orchestration logic
