# run_agent.py - The final, fully integrated script

import json
import logging
import time
from datetime import datetime
from .config import load_and_validate_config
from .linkedin_module import setup_driver, login_to_linkedin, search_and_process_profiles
from .repository import get_high_scoring_examples, save_validated_profile

# --- LangChain and Pydantic Imports ---
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field # Use Pydantic v2 for compatibility with latest LangChain
from langchain_google_vertexai import ChatVertexAI

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

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
    logging.info("Analyzing profile with LangChain...")
    
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
        logging.error(f"An error occurred during LangChain analysis: {e}")
        return None

# =============================================================================
# 3. FINAL, INTEGRATED MAIN WORKFLOW
# =============================================================================
def run_agent_with_parameters(query: str, location: str):
    """Runs the full agent workflow with a specific query and location."""
    # Load credentials and configuration
    config = load_and_validate_config()
    if not config:
        logging.error("Agent run aborted due to missing configuration.")
        return

    logging.info(f"--- Starting Agent for Query: '{query}' in '{location}' ---")

    # The mission is now defined directly by user input
    mission_critical_profile = {
        'search_query': query,
        'location': location
    }

    # Fetch examples from the database to guide the AI
    logging.info("Fetching top 2 high-scoring examples from the database...")
    examples = get_high_scoring_examples(limit=2)
    if examples:
        logging.info(f"Successfully fetched {len(examples)} examples.")

    # The main agent loop
    driver = None
    try:
        for attempt in range(1, 4):
            logging.info(f"--- Step 1: Setting up single browser session (Attempt {attempt}/3) ---")
            driver = setup_driver(headless=True)
            if driver:
                break
            logging.warning(f"Retrying in 5 seconds...")
            time.sleep(5)
        
        if not driver:
            logging.error("Failed to set up driver after multiple attempts. Aborting.")
            return

        login_to_linkedin(driver, config['linkedin_username'], config['linkedin_password'])

        # The core task: search, analyze, and save profiles
        search_and_process_profiles(
            driver=driver,
            mission_critical_profile=mission_critical_profile,
            examples=examples,
            save_callback=save_validated_profile
        )

    except Exception as e:
        logging.error(f"An unexpected error occurred during the agent run: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()
        logging.info("Agent run finished. Browser session closed.")

if __name__ == "__main__":
    # This allows the script to be run directly for testing purposes.
    # The main entry point for the package is now cli.py.
    # You can specify a default job name for direct execution.
    run_agent_with_parameters('linkedin_recruiter_search', 'New York')
