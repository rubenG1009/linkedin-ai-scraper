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
            text=True,
            env={'PGPASSWORD': 'test'}
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

def save_recruiter_analysis(profile_url: str, profile_text: str, mcp_data: dict, analysis_data: dict) -> bool:
    """Saves the recruiter analysis data to the validated_recruiters table."""
    try:
        # Convert dicts to JSON strings and escape single quotes for safe SQL insertion.
        profile_text_sql = profile_text.replace("'", "''")
        mcp_data_sql = json.dumps(mcp_data).replace("'", "''")
        analysis_data_sql = json.dumps(analysis_data).replace("'", "''")

        # Use INSERT with ON CONFLICT to either insert a new record or update an existing one.
        command = f"""
            INSERT INTO validated_recruiters (profile_url, profile_text, mcp_data, analysis_data, created_at)
            VALUES ('{profile_url}', '{profile_text_sql}', '{mcp_data_sql}', '{analysis_data_sql}', CURRENT_TIMESTAMP)
            ON CONFLICT (profile_url) DO UPDATE SET
                profile_text = EXCLUDED.profile_text,
                mcp_data = EXCLUDED.mcp_data,
                analysis_data = EXCLUDED.analysis_data,
                created_at = CURRENT_TIMESTAMP;
        """
        
        run_psql_command(command)
        return True
    except Exception as e:
        print(f"Error saving recruiter analysis: {e}")
        return False

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
