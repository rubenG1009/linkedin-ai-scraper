# 🤖 LinkedIn AI-Powered Recruitment Agent

**An autonomous agent that finds, analyzes, and scores potential recruitment candidates on LinkedIn using AI.**

---

### Overview

This project is a sophisticated, AI-driven software agent designed to automate the early stages of the recruitment pipeline. It intelligently searches LinkedIn for profiles matching a specific job query (e.g., "AI Recruiter in Spain"), scrapes the relevant profile data, uses Google's Vertex AI to analyze and score the profile's alignment with the role, and stores the validated candidates in a PostgreSQL database for review.

### ✨ Key Features

- **Autonomous Searching:** Runs automated, targeted searches on LinkedIn.
- **Intelligent Scraping:** Extracts key information from public LinkedIn profiles.
- **AI-Powered Analysis:** Leverages Google's Vertex AI for deep profile analysis and scoring.
- **Data Persistence:** Stores validated and scored candidates in a PostgreSQL database.
- **Professional CLI:** Packaged as a robust command-line tool (`linkedin-agent`).
- **Interactive Setup:** A user-friendly `configure` command for easy first-time setup.
- **Resilient & Robust:** Built with retry logic and headless browsing to handle real-world instability.

### 🛠️ Tech Stack

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Selenium](https://img.shields.io/badge/-selenium-%43B02A?style=for-the-badge&logo=selenium&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)

### 🚀 Getting Started

Follow these steps to get the agent up and running on your local machine.

#### 1. Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [Google Chrome](https://www.google.com/chrome/)

#### 2. Installation

First, clone the repository to your local machine:
```bash
git clone <your-repository-url>
cd linkedin-ai-scraper
```

Next, it is highly recommended to create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Now, install the required dependencies and the agent's CLI package:
```bash
# Install all required libraries
pip install -r requirements.txt

# Install the CLI in editable mode
pip install -e .
```

#### 3. Configuration

This project uses a simple interactive command to set up your credentials securely. Run the following command:

```bash
linkedin-agent configure
```

The tool will prompt you for:
- Your LinkedIn Email
- Your LinkedIn Password
- Your Database Connection Details

This will create a `.env` file in the root of the project, which the agent will use to run.

### Usage

Once the configuration is complete, you can run the agent with a single command:

```bash
linkedin-agent run
```

The agent will start its process in the background (headless mode). You can monitor its progress in the terminal and see the results appear in your PostgreSQL database.
