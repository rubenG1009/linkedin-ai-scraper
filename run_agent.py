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
from repository import get_job_schedule, save_recruiter_analysis

# 2. From your Selenium automation file
from linkedin_module import (
    setup_driver, 
    _login_to_linkedin, # Now need the login function directly
    LINKEDIN_USERNAME,  # Need credentials
    LINKEDIN_PASSWORD,
    perform_search_and_get_urls, 
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
def analyze_profile_with_langchain(profile_text: str, mcp_data: dict):
    """
    Analyzes profile text using a LangChain chain with a dynamic prompt and structured output.
    """
    print("Analyzing profile with LangChain...")
    
    # --- Setup the Parser ---
    pydantic_parser = PydanticOutputParser(pydantic_object=RecruiterAnalysis)
    format_instructions = pydantic_parser.get_format_instructions()

    # --- Setup the Prompt ---
    prompt_template = """
    You are an expert technical recruiter. Your task is to analyze the provided LinkedIn profile text and determine if the candidate is a good fit for a specific role.

    **Evaluation Criteria (from Mission Critical Profile):**
    - Search Query: {search_query}
    - Location: {location}

    **Candidate's Profile Text:**
    {profile_text}

    **Your Task:**
    1.  Carefully read the profile text.
    2.  Compare the candidate's experience against the evaluation criteria.
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
        partial_variables={"format_instructions": format_instructions}
    )

    # --- Setup the LLM and Chain ---
    # Using the specified Gemini model
    llm = ChatVertexAI(
        model_name="gemini-pro", 
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
def main():
    """
    Main function to run the complete, integrated intelligent agent workflow.
    This version is designed for stability by using a fresh browser session for each profile.
    """
    JOB_NAME = 'linkedin_recruiter_search'
    
    # --- Load the Mission from the Database ---
    print(f"--- Starting Agent Workflow for Job: {JOB_NAME} ---")
    job_schedule = get_job_schedule(JOB_NAME)
    if not job_schedule or "mission_parameters" not in job_schedule:
        print(f"Could not load job or mission parameters for '{JOB_NAME}'. Exiting.")
        return
        
    mcp_data = job_schedule["mission_parameters"]
    print(f"Successfully loaded Mission Critical Profile: {mcp_data}")

    # --- STEP 1: Get all profile URLs in a single session ---
    profile_urls = []
    initial_driver = None
    try:
        print("\n--- Step 1: Getting all profile URLs ---")
        initial_driver = setup_driver()
        search_query = mcp_data.get("search_query", "Technical Recruiter")
        profile_urls = perform_search_and_get_urls(initial_driver, search_query)
    except Exception as e:
        print(f"A critical error occurred during URL collection: {e}")
    finally:
        if initial_driver:
            print("Closing initial driver.")
            initial_driver.quit()

    if not profile_urls:
        print("No profile URLs found. Exiting workflow.")
        print("\n--- Agent Workflow Complete ---")
        return

    # --- STEP 2: Process each profile in its own isolated session ---
    print(f"\n--- Step 2: Processing {len(profile_urls)} profiles one by one for stability ---")
    for url in profile_urls:
        driver = None
        try:
            print(f"\n--- Processing Profile: {url} ---")
            
            # Start a fresh driver and log in for this specific profile
            driver = setup_driver()
            if not _login_to_linkedin(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
                print(f"Could not log in to process {url}. Skipping.")
                continue # Skip to the next profile

            # Scrape full details
            profile_text = scrape_full_profile_details(driver, url)
            if not profile_text:
                print(f"Could not scrape details for {url}. Skipping.")
                continue

            # Analyze the profile with LangChain
            analysis = analyze_profile_with_langchain(profile_text, mcp_data)
            
            if analysis:
                print("--- LangChain Analysis Result ---")
                analysis_dict = analysis.model_dump()
                print(json.dumps(analysis_dict, indent=2))
                
                # Save the final analysis to PostgreSQL
                print("Saving analysis to PostgreSQL...")
                save_recruiter_analysis(
                    profile_url=url,
                    profile_text=profile_text,
                    mcp_data=mcp_data,
                    analysis_data=analysis_dict
                )
                print("Save complete.")
        
        except Exception as e:
            print(f"A critical error occurred while processing {url}: {e}")
        
        finally:
            # Clean up the driver for this specific profile
            if driver:
                print(f"Closing driver for profile: {url}")
                driver.quit()
            
            # Add a polite delay to avoid overwhelming LinkedIn
            print("Pausing for 5 seconds before next profile...")
            time.sleep(5)

    print("\n--- Agent Workflow Complete ---")

if __name__ == "__main__":
    main()
