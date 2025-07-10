#!/bin/bash
#
# This script provides a simple way to run the LinkedIn Scraper & AI Analyzer agent.
# It ensures that the required environment variables are set and that the agent is run
# using the Python interpreter from the project's virtual environment.

# Activate the virtual environment
source venv/bin/activate

# Set the Google Cloud credentials environment variable and run the agent
GOOGLE_APPLICATION_CREDENTIALS="gcp-linkedin-agent-credentials.json" venv/bin/python3 run_agent.py
