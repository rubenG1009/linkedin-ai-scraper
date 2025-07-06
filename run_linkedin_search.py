import time
import datetime
from repository import get_job_schedule, update_next_run_timestamp

def should_run_job(job_schedule: dict) -> bool:
    """Determine if it's time to run the job based on its schedule."""
    if not job_schedule:
        return False
    
    if not job_schedule['is_active'] == 't':
        return False
        
    # Convert next_run_timestamp_ms to a datetime
    next_run_time = datetime.datetime.fromtimestamp(
        int(job_schedule['next_run_timestamp_ms']) / 1000,
        datetime.timezone.utc
    )
    
    # Get current time in UTC
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    # Check if current time is equal to or after next_run_time
    return current_time >= next_run_time

def run_linkedin_search():
    """Simulate running the LinkedIn search process."""
    print("Running LinkedIn search...")
    # TODO: Implement actual LinkedIn search logic here
    return "Success", "LinkedIn search completed successfully"

def update_job_status(job_name: str, status: str, message: str):
    """Update the job's status and message."""
    current_time_ms = int(time.time() * 1000)
    update_next_run_timestamp(job_name, current_time_ms)
    print(f"Updated job status: {status}")
    print(f"Message: {message}")

def main():
    try:
        # Get the job schedule
        job_schedule = get_job_schedule('linkedin_recruiter_search')
        
        if not job_schedule:
            print("Job schedule not found")
            return
            
        if should_run_job(job_schedule):
            print("Time to run LinkedIn search!")
            
            # Run the search
            status, message = run_linkedin_search()
            
            # Update the job status
            update_job_status('linkedin_recruiter_search', status, message)
            
        else:
            print("Not time to run LinkedIn search yet")
            
    except Exception as e:
        print(f"Error in main process: {e}")

if __name__ == "__main__":
    main()
