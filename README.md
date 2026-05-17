# 🤖 LinkedIn AI-Powered Recruitment Agent

> Automate LinkedIn candidate sourcing with AI scoring — built with Python, LangChain, Google Vertex AI and PostgreSQL.

An end-to-end recruitment automation agent that searches LinkedIn for candidate profiles, 
uses Google's Vertex AI to score their fit for a role, and persists everything in a 
PostgreSQL database — all from a single CLI command.

Built as a real-world automation project combining web scraping, LLM-powered analysis 
and relational database storage.

---

## ✨ Key Features

- **Automated LinkedIn Scraping** — Navigates LinkedIn, performs searches and extracts profile data using Selenium with robust error handling for dynamic content
- **AI-Powered Candidate Scoring** — Uses LangChain + Google Vertex AI to analyze profile text and score each candidate against custom job requirements
- **CLI Interface** — Run the full agent with a single command, passing custom queries and location filters
- **PostgreSQL Storage** — Stores scraped data and AI analysis results for persistence and further querying
- **Resilient by design** — Built with modern scraping techniques and error handling to handle LinkedIn's dynamic rendering

---

## 🏗️ Architecturegic

CLI command
↓
linkedin_module.py   →   Selenium scrapes LinkedIn profiles
↓
langchain_module.py  →   Vertex AI scores candidate fit
↓
repository.py        →   Results saved to PostgreSQL


---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL (running instance)
- Google Cloud SDK (for Vertex AI)
- ChromeDriver (matching your Chrome version)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/rubenG1009/linkedin-ai-scraper.git
cd linkedin-ai-scraper

# 2. Install dependencies
pip install -r requirements.txt

# 3. (macOS) Install Google Cloud SDK
brew install --cask google-cloud-sdk

# 4. Authenticate with Google Cloud
gcloud auth application-default login
```

### Configuration

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|---|---|
| `LINKEDIN_USERNAME` | Your LinkedIn email |
| `LINKEDIN_PASSWORD` | Your LinkedIn password |
| `CHROMEDRIVER_PATH` | Absolute path to your chromedriver |
| `DB_USER / DB_PASSWORD / DB_HOST / DB_PORT / DB_NAME` | PostgreSQL connection details |

```bash
# Set up the database schema
psql -U your_user -d your_db -f database/create_tables.sql
```

---

## 🖥️ Usage

```bash
python -m linkedin_agent.cli run --query "Python Developer" --location "Remote"
```

The agent will log in to LinkedIn, run the search, scrape profiles, score them with AI and save results to your database.

---

## 📂 Project Structure

.
├── .env.example
├── requirements.txt
├── database/
│   └── create_tables.sql
└── linkedin_agent/
├── cli.py                # CLI entrypoint (argparse)
├── linkedin_module.py    # Selenium scraping logic
├── langchain_module.py   # Vertex AI / LangChain analysis
├── repository.py         # PostgreSQL interactions
└── run_agent.py          # Main orchestration

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-000000?style=flat-square&logo=langchain&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Vertex_AI-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=flat-square&logo=selenium&logoColor=white)

---

## ⚠️ Disclaimer

This project is built for educational and research purposes. 
Use responsibly and in accordance with LinkedIn's Terms of Service.

---

## 👤 Author

**Rubén García Revett** — [LinkedIn](https://www.linkedin.com/in/ruben-garcia-revett-b72312223/) · [GitHub](https://github.com/rubenG1009)
