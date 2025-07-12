import click
from .run_agent import main as run_agent_main

@click.group()
def cli():
    """A CLI for the LinkedIn Scraper Agent."""
    pass

@cli.command()
@click.argument('job_name', default='linkedin_recruiter_search')
def run(job_name):
    """Runs the LinkedIn agent for a specific job."""
    click.echo(f"INFO: Starting agent for job: {job_name}")
    try:
        run_agent_main(job_name)
        click.echo(f"INFO: Agent finished job: {job_name}")
    except Exception as e:
        click.echo(f"ERROR: An error occurred during agent execution: {e}", err=True)

if __name__ == '__main__':
    cli()
