import subprocess
import json
from typing import Optional, Dict, Any
from datetime import datetime

def run_psql_command(command: str) -> str:
    """Run a psql command and return the output."""
    try:
        result = subprocess.run(
            ['/opt/homebrew/bin/psql', '-h', 'localhost', '-U', 'rubeng', '-d', 'rubeng', '-At', '-c', command],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"psql command failed: {result.stderr}")
            
        # Clean up the output by removing extra whitespace and newlines
        output = result.stdout.strip()
        return output if output else None
    except Exception as e:
        print(f"Error running psql command: {e}")
        raise

def get_job_schedule(job_name: str) -> Optional[Dict]:
    """Retrieve a specific job schedule by name, including mission parameters."""
    try:
        # The -At flag gives us a pipe-separated output. Added 'mission_parameters'.
        result = run_psql_command(f"""
            SELECT job_name, is_active, last_run_status, last_run_message,
                   created_at, updated_at, next_run_timestamp_ms, mission_parameters
            FROM job_schedules
            WHERE job_name = '{job_name}'
        """)
        
        if not result:  # No rows returned
            return None
            
        # Split the pipe-separated values
        values = result.split('|')
        if len(values) != 8:  # Expect 8 columns now
            raise ValueError(f"Unexpected number of values returned. Expected 8, got {len(values)}")
            
        # Clean up the values by removing extra whitespace
        cleaned_values = [v.strip() for v in values]

        # The 8th value is the mission_parameters JSON string. Parse it.
        mission_params_json = cleaned_values[7]
        mission_parameters = json.loads(mission_params_json) if mission_params_json else None
        
        return {
            'job_name': cleaned_values[0],
            'is_active': cleaned_values[1],
            'last_run_status': cleaned_values[2],
            'last_run_message': cleaned_values[3],
            'created_at': cleaned_values[4],
            'updated_at': cleaned_values[5],
            'next_run_timestamp_ms': cleaned_values[6],
            'mission_parameters': mission_parameters  # Add the parsed dictionary
        }
    except Exception as e:
        print(f"Error retrieving job schedule: {e}")
        return None

def profile_url_exists(profile_url: str) -> bool:
    """Checks if a profile URL already exists in the validated_recruiters table."""
    try:
        result = run_psql_command(f"""
            SELECT EXISTS(SELECT 1 FROM validated_recruiters WHERE profile_url='{profile_url}')
        """)
        exists = result.strip().lower() == 't'
        return exists
    except Exception as e:
        print(f"Error checking profile URL existence: {e}")
        return False

def save_recruiter_analysis(profile_url: str, profile_text: str, mcp_data: dict, analysis_data: dict) -> bool:
    """Saves the recruiter analysis data, including the dedicated alignment_score, to the validated_recruiters table."""
    try:
        # Convert dicts to JSON strings and escape single quotes for safe SQL insertion.
        profile_text_sql = profile_text.replace("'", "''")
        mcp_data_sql = json.dumps(mcp_data).replace("'", "''")
        analysis_data_sql = json.dumps(analysis_data).replace("'", "''")
        alignment_score = analysis_data.get('alignment_score', 'NULL') # Use NULL as a default if score is missing

        # Use INSERT with ON CONFLICT to either insert a new record or update an existing one.
        command = f"""
            INSERT INTO validated_recruiters (profile_url, profile_text, mcp_data, analysis_data, alignment_score, created_at)
            VALUES ('{profile_url}', '{profile_text_sql}', '{mcp_data_sql}', '{analysis_data_sql}', {alignment_score}, CURRENT_TIMESTAMP)
            ON CONFLICT (profile_url) DO UPDATE SET
                profile_text = EXCLUDED.profile_text,
                mcp_data = EXCLUDED.mcp_data,
                analysis_data = EXCLUDED.analysis_data,
                alignment_score = EXCLUDED.alignment_score,
                created_at = CURRENT_TIMESTAMP;
        """
        
        run_psql_command(command)
        return True
    except Exception as e:
        print(f"Error saving recruiter analysis: {e}")
        return False

def get_high_scoring_examples(limit: int = 2) -> list:
    """Retrieves the top N profiles with the highest alignment scores to use as few-shot examples."""
    print(f"Fetching top {limit} high-scoring examples from the database...")
    try:
        # This query constructs a JSON object for each row and aggregates them into a single JSON array.
        # This is much safer and cleaner than trying to parse the psql text table output.
        command = f"""
        SELECT json_agg(t) FROM (
            SELECT profile_text, analysis_data
            FROM validated_recruiters
            WHERE alignment_score IS NOT NULL
            ORDER BY alignment_score DESC
            LIMIT {limit}
        ) t; 
        """
        
        # Execute the command and get the raw JSON output
        json_output_str = run_psql_command(command)
        
        if not json_output_str or json_output_str.strip() == "":
            print("No examples found in the database.")
            return []

        # The output from psql might contain headers or footers, so we find the JSON array
        json_start = json_output_str.find('[')
        json_end = json_output_str.rfind(']') + 1
        if json_start == -1 or json_end == 0:
            print("Could not find a valid JSON array in the psql output.")
            return []

        clean_json_str = json_output_str[json_start:json_end]
        examples = json.loads(clean_json_str)
        
        # The analysis_data is a string inside the JSON, so we need to parse it too.
        for example in examples:
            if isinstance(example.get('analysis_data'), str):
                example['analysis'] = json.loads(example['analysis_data'])
            else:
                example['analysis'] = example.get('analysis_data')

        print(f"Successfully fetched {len(examples)} examples.")
        return examples

    except Exception as e:
        print(f"Error fetching high-scoring examples: {e}")
        return []

def update_next_run_timestamp(job_name: str, timestamp_ms: int) -> bool:
    """Update the next_run_timestamp_ms for a job."""
    try:
        result = run_psql_command(f"""
            UPDATE job_schedules 
            SET next_run_timestamp_ms = {timestamp_ms}, 
                updated_at = CURRENT_TIMESTAMP
            WHERE job_name = '{job_name}'
        """)
        return "UPDATE 1" in result  # PostgreSQL returns "UPDATE 1" when successful
    except Exception as e:
        print(f"Error updating next_run_timestamp_ms: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Replace these with your actual database credentials
    DB_CONFIG = {
        'dbname': 'my_project',
        'user': 'postgres',
        'password': 'test',
        'host': 'my-postgres.myapp_network',
        'port': '5432'
    }
    
    # Test getting a job schedule
    job = get_job_schedule('linkedin_recruiter_search')
    if job:
        print("Found job schedule:")
        print(job)
    else:
        print("Job schedule not found")

    # Test updating next_run_timestamp_ms
    import time
    current_time_ms = int(time.time() * 1000)  # Convert current time to milliseconds
    success = update_next_run_timestamp('linkedin_recruiter_search', current_time_ms)
    if success:
        print("Successfully updated next_run_timestamp_ms")
    else:
        print("Failed to update next_run_timestamp_ms")
