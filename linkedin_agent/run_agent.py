# run_agent.py - The final, fully integrated script

import json

# --- LangChain and Pydantic Imports ---
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field # Use Pydantic v2 for compatibility with latest LangChain
from langchain_google_vertexai import ChatVertexAI

# --- Import Your Real, Working Functions and Classes ---
# 1. From your database repository file
import time
from datetime import datetime
from .repository import get_job_schedule, save_recruiter_analysis, profile_url_exists, get_high_scoring_examples

# 2. From your Selenium automation file
from .linkedin_module import (
    setup_driver,
    _login_to_linkedin,
    LINKEDIN_USERNAME,
    LINKEDIN_PASSWORD,
    search_for_people,
    extract_urls_from_current_page,
    click_next_page,
    scrape_full_profile_details
)

# =============================================================================
# 1. DEFINE THE LLM'S OUTPUT DATA STRUCTURE (PYDANTIC MODEL)
# =============================================================================
class RecruiterAnalysis(BaseModel):
    """Data structure for the structured output from the LLM analysis."""
    summary: str = Field(description="A brief, one-paragraph summary of the candidate's professional background.")
    alignment_score: int = Field(description="A score from 1 (poor fit) to 10 (perfect fit) based on the evaluation criteria.")
    justification: str = Field(description="A brief explanation for the alignment score, referencing the provided keywords.")
    recommendation: str = Field(description="A clear 'Recommend' or 'Do Not Recommend' decision.")

# =============================================================================
# 2. LANGCHAIN ANALYSIS FUNCTION
# =============================================================================
def analyze_profile_with_langchain(profile_text: str, mcp_data: dict, few_shot_examples: list = None):
    """
    Analyzes profile text using a LangChain chain with a dynamic prompt, structured output,
    and optional few-shot examples for improved accuracy.
    """
    print("Analyzing profile with LangChain...")
    
    # --- Setup the Parser ---
    pydantic_parser = PydanticOutputParser(pydantic_object=RecruiterAnalysis)
    format_instructions = pydantic_parser.get_format_instructions()

    # --- Build Few-Shot Examples Section ---
    examples_section = ""
    if few_shot_examples:
        examples_section += "\n**Here are some examples of high-quality analyses:**\n"
        for i, example in enumerate(few_shot_examples):
            # Ensure the nested analysis is a dict, not a string
            analysis_json = example.get('analysis', {})
            if isinstance(analysis_json, str):
                try:
                    analysis_json = json.loads(analysis_json)
                except json.JSONDecodeError:
                    analysis_json = {}

            score = analysis_json.get('alignment_score', 'N/A')
            examples_section += f"\n--- Example {i+1} (Score: {score}) ---\n"
            examples_section += f"**Profile Text:**\n{example.get('profile_text', 'N/A')}\n"
            examples_section += f"**Expected Analysis:**\n{json.dumps(analysis_json, indent=2)}\n"
        examples_section += "\n--- End of Examples ---\n"

    # --- Setup the Prompt ---
    prompt_template = """
    You are an expert technical recruiter. Your task is to analyze the provided LinkedIn profile text and determine if the candidate is a good fit for a specific role.

    **Evaluation Criteria (from Mission Critical Profile):**
    - Search Query: {search_query}
    - Location: {location}

    {examples_section}

    **Now, analyze the following new candidate based on the same criteria.**

    **Candidate's Profile Text:**
    {profile_text}

    **Your Task:**
    1.  Carefully read the new profile text.
    2.  Compare the candidate's experience against the evaluation criteria, using the examples for guidance on quality and format.
    3.  Provide a concise summary of the candidate's background.
    4.  Give an alignment score from 1 (poor fit) to 10 (perfect fit).
    5.  Justify the score with a brief explanation.
    6.  Make a clear 'Recommend' or 'Do Not Recommend' decision.

    **Output Format:**
    {format_instructions}
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["profile_text", "search_query", "location"],
        partial_variables={
            "format_instructions": format_instructions,
            "examples_section": examples_section
        }
    )

    # --- Setup the LLM and Chain ---
    # Using the specified Gemini model
    llm = ChatVertexAI(
        model_name="gemini-2.5-pro", 
        project="my-linkedin-agent-v2", 
        location="us-central1"
    )
    
    chain = prompt | llm | pydantic_parser

    # --- Run the Chain ---
    try:
        # Extract mission parameters for the prompt
        search_query = mcp_data.get("search_query", "N/A")
        location = mcp_data.get("location", "N/A")

        response = chain.invoke({
            "profile_text": profile_text,
            "search_query": search_query,
            "location": location,
        })
        return response
    except Exception as e:
        print(f"An error occurred during LangChain analysis: {e}")
        return None

# =============================================================================
# 3. FINAL, INTEGRATED MAIN WORKFLOW
# =============================================================================
def main(job_name: str):
    """
    Main function to run a fast, single-session simulation of the agent.
    This version logs in once and processes all profiles in the same browser.
    """
    # --- Load the Mission from the Database ---
    print(f"--- Starting Agent Simulation for Job: {job_name} ---")
    job_schedule = get_job_schedule(job_name)

    # --- DEBUG: Print the raw job schedule from the database ---
    print(f"DEBUG: Raw job schedule from DB: {job_schedule}")

    if not job_schedule or not job_schedule.get("mission_parameters"):
        print(f"Could not load job or mission parameters for '{job_name}'. Exiting.")
        return

    # --- Check if the job is actually due to run ---
    current_time_ms = int(datetime.now().timestamp() * 1000)
    next_run_ms = int(job_schedule.get('next_run_timestamp_ms') or 0)

    if current_time_ms < next_run_ms:
        print(f"Job '{job_name}' is not scheduled to run yet. Exiting.")
        return
        
    mcp_data = job_schedule["mission_parameters"]
    print(f"Successfully loaded Mission Critical Profile: {mcp_data}")

    # --- Fetch Few-Shot Examples ONCE at the start ---
    few_shot_examples = get_high_scoring_examples(limit=2)

    # --- Main Simulation Block (Single Session) ---
    driver = None
    # Add a retry loop for driver setup to handle intermittent failures
    for attempt in range(3):
        try:
            # --- Step 1: Set up a single browser session ---
            print(f"\n--- Step 1: Setting up single browser session (Attempt {attempt + 1}/3) ---")
            driver = setup_driver()
            if driver:
                print("Driver setup successful.")
                break  # Exit the loop if driver is set up successfully
        except Exception as e:
            print(f"Error setting up driver on attempt {attempt + 1}: {e}")
            if attempt < 2:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("Failed to set up driver after multiple attempts. Aborting.")
                return

    if not driver:
        return

    try:
        if not _login_to_linkedin(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
            print("Could not log in. Aborting simulation.")
            return

        # --- Step 2: Perform Initial Search ---
        print("\n--- Step 2: Performing initial search ---")
        search_query = mcp_data.get("search_query", "Technical Recruiter")
        if not search_for_people(driver, search_query):
            print("Failed to load initial search results. Aborting.")
            return

        # --- Step 3: Paginate and Process Profiles ---
        print("\n--- Step 3: Processing profiles page by page ---")
        page_number = 1
        while True:
            print(f"\n--- Processing Page {page_number} ---")
            
            # Extract URLs from the current page
            profile_urls_on_page = extract_urls_from_current_page(driver)
            
            if not profile_urls_on_page:
                print("No profile URLs found on this page. Checking for next page or finishing.")

            # Process the URLs found on the current page
            for url in profile_urls_on_page:
                try:
                    if profile_url_exists(url):
                        print(f"INFO: Skipping profile {url} as it has already been processed.", flush=True)
                        continue

                    print(f"\n--- Processing Profile: {url} ---", flush=True)
                    profile_text = scrape_full_profile_details(driver, url)
                    if not profile_text:
                        print(f"Could not scrape details for {url}. Skipping.", flush=True)
                        continue

                    analysis = analyze_profile_with_langchain(profile_text, mcp_data, few_shot_examples)
                    if not analysis:
                        print(f"Could not analyze profile {url}. Skipping.", flush=True)
                        continue

                    print("--- LangChain Analysis Result ---")
                    analysis_dict = analysis.model_dump()
                    print(json.dumps(analysis_dict, indent=2))

                    print("Saving analysis to PostgreSQL...")
                    save_recruiter_analysis(
                        profile_url=url,
                        profile_text=profile_text,
                        mcp_data=mcp_data,
                        analysis_data=analysis_dict
                    )
                    print("Save complete.")
                    print("Pausing for 2 seconds before next profile...")
                    time.sleep(2)

                except Exception as e:
                    print(f"An error occurred while processing {url}: {e}. Skipping to next profile.", flush=True)

            # Try to go to the next page
            if not click_next_page(driver):
                break # Exit the while loop if it was the last page
            
            page_number += 1
            
    except Exception as e:
        print(f"A critical error occurred during the simulation: {e}")
    
    finally:
        # Clean up the single driver at the very end
        if driver:
            print("\nClosing browser session.")
            driver.quit()
        
        print("\n--- Agent Simulation Complete ---")

if __name__ == "__main__":
    # This allows the script to be run directly for testing purposes.
    # The main entry point for the package is now cli.py.
    # You can specify a default job name for direct execution.
    main('linkedin_recruiter_search')
