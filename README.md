# 🤖 LinkedIn AI Scraper

Automated agent that scrapes LinkedIn for candidate profiles, uses Google Vertex AI to analyze their suitability for a role, and stores the results in a PostgreSQL database — all from a single CLI command.

## 🚀 What it does

You define a search query and job requirements. The agent:
1. Navigates LinkedIn and extracts candidate profile data automatically
2. Sends that data to **Google Vertex AI via LangChain** to score each candidate against your requirements
3. Saves the profiles + AI analysis to a **PostgreSQL database** for filtering and follow-up

No manual copy-pasting. No spreadsheets. Just results.

## 🛠️ Tech Stack

- **Python** — core language
- **Selenium** — LinkedIn navigation and scraping
- **LangChain + Google Vertex AI** — AI-powered candidate analysis
- **PostgreSQL** — persistent storage of results
- **argparse CLI** — simple command-line interface

## 📁 Project Structure
