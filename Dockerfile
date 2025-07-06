FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY repository.py .
COPY run_linkedin_search.py .

CMD ["python", "run_linkedin_search.py"]docker build -t postgres-python-test .
