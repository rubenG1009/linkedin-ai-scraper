#!/bin/bash
cd "$(dirname "$0")"
while true; do
  bash test_script.sh >> cron.log 2>&1
  sleep 60
done
