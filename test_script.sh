#!/bin/bash
echo "Starting test at $(date)" > cron.log
echo "Running Python script..." >> cron.log
cd "$(dirname "$0")"
./venv/bin/python run_linkedin_search.py >> cron.log 2>&1
