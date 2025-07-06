#!/bin/bash
PGPASSWORD=test psql -h localhost -U postgres -d my_project -c "SELECT 1"
