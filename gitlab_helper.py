#!/usr/bin/env python3

import sys
import json
import typer
from typing import Optional, Dict, List, Any
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.progress import Progress, SpinnerColumn, TextColumn
from gitlab_client import GitLabClient

app = typer.Typer(help="GitLab CI/CD pipeline helper")
pipelines_app = typer.Typer(help="Manage GitLab pipelines")
jobs_app = typer.Typer(help="Manage GitLab jobs")
app.add_typer(pipelines_app, name="pipelines")
app.add_typer(jobs_app, name="jobs")

console = Console()

# Initialize GitLab client
def get_client(config_path: Optional[str] = None) -> GitLabClient:
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Connecting to GitLab..."),
        transient=True,
    ) as progress:
        progress.add_task("connect", total=None)
        return GitLabClient(config_path)

@pipelines_app.command("list")
def list_pipelines(
    limit: int = typer.Option(10, help="Number of pipelines to show"),
    config_path: Optional[str] = typer.Option(None, help="Path to config file")
):
    """List recent GitLab pipelines"""
    client = get_client(config_path)
    pipelines = client.get_pipelines(limit=limit)
    client.display_pipelines(pipelines)

@pipelines_app.command("latest")
def get_latest_pipeline(
    config_path: Optional[str] = typer.Option(None, help="Path to config file")
):
    """Get the latest pipeline"""
    client = get_client(config_path)
    pipeline = client.get_latest_pipeline()
    if pipeline:
        client.display_pipelines([pipeline])
    else:
        console.print("[bold red]No pipelines found[/bold red]")

@pipelines_app.command("status")
def get_pipeline_status(
    pipeline_id: int = typer.Argument(..., help="Pipeline ID"),
    config_path: Optional[str] = typer.Option(None, help="Path to config file")
):
    """Get status of a specific pipeline"""
    client = get_client(config_path)
    pipeline = client.get_pipeline(pipeline_id)
    if pipeline:
        client.display_pipelines([pipeline])
    else:
        console.print(f"[bold red]Pipeline {pipeline_id} not found[/bold red]")

@pipelines_app.command("create")
def create_pipeline(
    ref: str = typer.Option("main", help="Git reference (branch/tag)"),
    variables: Optional[str] = typer.Option(None, help="Pipeline variables in JSON format, e.g. '{\"VAR1\": \"value1\"}'"),
    config_path: Optional[str] = typer.Option(None, help="Path to config file")
):
    """Create a new pipeline"""
    client = get_client(config_path)
    
    vars_dict = None
    if variables:
        try:
            vars_dict = json.loads(variables)
        except json.JSONDecodeError:
            console.print("[bold red]Error: Variables must be valid JSON[/bold red]")
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Creating pipeline..."),
        transient=True,
    ) as progress:
        progress.add_task("create", total=None)
        pipeline = client.create_pipeline(ref=ref, variables=vars_dict)
    
    if pipeline:
        console.print(f"[bold green]Pipeline created successfully with ID: {pipeline.id}[/bold green]")
        client.display_pipelines([pipeline])
        
        # Automatically show jobs
        console.print("[bold]Jobs for this pipeline:[/bold]")
        jobs = client.get_jobs(pipeline.id)
        client.display_jobs(jobs)
    else:
        console.print("[bold red]Failed to create pipeline[/bold red]")

@jobs_app.command("list")
def list_jobs(
    pipeline_id: int = typer.Argument(..., help="Pipeline ID"),
    config_path: Optional[str] = typer.Option(None, help="Path to config file")
):
    """List jobs for a specific pipeline"""
    client = get_client(config_path)
    jobs = client.get_jobs(pipeline_id)
    if jobs:
        client.display_jobs(jobs)
    else:
        console.print(f"[bold red]No jobs found for pipeline {pipeline_id}[/bold red]")

@jobs_app.command("logs")
def get_job_logs(
    job_id: int = typer.Argument(..., help="Job ID"),
    config_path: Optional[str] = typer.Option(None, help="Path to config file"),
    raw: bool = typer.Option(True, help="Display raw logs with original formatting")
):
    """Get logs for a specific job"""
    try:
        client = get_client(config_path)
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Fetching job logs..."),
            transient=True,
        ) as progress:
            progress.add_task("logs", total=None)
            logs = client.get_job_logs(job_id)
        
        if logs:
            if raw:
                # Output logs directly to preserve ANSI color codes
                print(f"\n--- Logs for Job #{job_id} ---")
                print(logs)
                print("-----------------------------")
            else:
                # Use rich's syntax highlighting (loses GitLab's color formatting)
                syntax = Syntax(logs, "bash", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"Logs for Job #{job_id}", expand=False))
        else:
            console.print(f"[bold red]No logs found for job {job_id}[/bold red]")
    except ValueError:
        console.print(f"[bold red]Error: Job ID '{job_id}' is not a valid integer[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")

@app.command("interactive")
def interactive_mode(
    config_path: Optional[str] = typer.Option(None, help="Path to config file")
):
    """Start interactive console mode"""
    client = get_client(config_path)
    
    console.print("[bold blue]===== GitLab CI/CD Helper Interactive Mode =====[/bold blue]")
    console.print("Type 'exit' or 'quit' to exit the application")
    
    session = PromptSession()
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })
    
    # Main menu options
    main_menu_options = [
        "list-pipelines", 
        "latest-pipeline", 
        "create-pipeline", 
        "pipeline-status", 
        "list-jobs", 
        "job-logs", 
        "help", 
        "exit"
    ]
    main_completer = WordCompleter(main_menu_options)
    
    current_pipeline_id = None
    current_job_id = None
    
    while True:
        try:
            user_input = session.prompt(
                "gitlab> ", 
                completer=main_completer,
                style=style
            )
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            elif user_input.lower() == 'help':
                console.print("[bold cyan]Available commands:[/bold cyan]")
                for cmd in main_menu_options:
                    if cmd != 'help' and cmd != 'exit':
                        console.print(f"  - {cmd}")
                        
            elif user_input.lower() == 'list-pipelines':
                limit = Prompt.ask("Number of pipelines to show", default="10")
                pipelines = client.get_pipelines(limit=int(limit))
                client.display_pipelines(pipelines)
                
                if pipelines:
                    select_pipeline = Confirm.ask("Select a pipeline?")
                    if select_pipeline:
                        pipeline_id = Prompt.ask("Enter pipeline ID")
                        current_pipeline_id = int(pipeline_id)
                        pipeline = client.get_pipeline(current_pipeline_id)
                        if pipeline:
                            client.display_pipelines([pipeline])
                            console.print("[bold]Jobs for this pipeline:[/bold]")
                            jobs = client.get_jobs(current_pipeline_id)
                            client.display_jobs(jobs)
                
            elif user_input.lower() == 'latest-pipeline':
                pipeline = client.get_latest_pipeline()
                if pipeline:
                    client.display_pipelines([pipeline])
                    current_pipeline_id = pipeline.id
                    console.print("[bold]Jobs for this pipeline:[/bold]")
                    jobs = client.get_jobs(current_pipeline_id)
                    client.display_jobs(jobs)
                else:
                    console.print("[bold red]No pipelines found[/bold red]")
                    
            elif user_input.lower() == 'create-pipeline':
                ref = Prompt.ask("Git reference (branch/tag)", default="main")
                
                use_vars = Confirm.ask("Add variables?")
                vars_dict = None
                
                if use_vars:
                    vars_json = Prompt.ask("Enter variables in JSON format, e.g. '{\"VAR1\": \"value1\"}'")
                    try:
                        vars_dict = json.loads(vars_json)
                    except json.JSONDecodeError:
                        console.print("[bold red]Error: Variables must be valid JSON[/bold red]")
                        continue
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Creating pipeline..."),
                    transient=True,
                ) as progress:
                    progress.add_task("create", total=None)
                    pipeline = client.create_pipeline(ref=ref, variables=vars_dict)
                
                if pipeline:
                    console.print(f"[bold green]Pipeline created successfully with ID: {pipeline.id}[/bold green]")
                    client.display_pipelines([pipeline])
                    current_pipeline_id = pipeline.id
                    
                    # Automatically show jobs
                    console.print("[bold]Jobs for this pipeline:[/bold]")
                    jobs = client.get_jobs(current_pipeline_id)
                    client.display_jobs(jobs)
                else:
                    console.print("[bold red]Failed to create pipeline[/bold red]")
                    
            elif user_input.lower() == 'pipeline-status':
                if current_pipeline_id:
                    use_current = Confirm.ask(f"Use current pipeline (ID: {current_pipeline_id})?")
                    if not use_current:
                        current_pipeline_id = int(Prompt.ask("Enter pipeline ID"))
                else:
                    current_pipeline_id = int(Prompt.ask("Enter pipeline ID"))
                
                pipeline = client.get_pipeline(current_pipeline_id)
                if pipeline:
                    client.display_pipelines([pipeline])
                else:
                    console.print(f"[bold red]Pipeline {current_pipeline_id} not found[/bold red]")
                    
            elif user_input.lower() == 'list-jobs':
                try:
                    if current_pipeline_id:
                        use_current = Confirm.ask(f"Use current pipeline (ID: {current_pipeline_id})?")
                        if not use_current:
                            pipeline_id = Prompt.ask("Enter pipeline ID")
                            current_pipeline_id = int(pipeline_id)
                    else:
                        pipeline_id = Prompt.ask("Enter pipeline ID")
                        current_pipeline_id = int(pipeline_id)
                    
                    jobs = client.get_jobs(current_pipeline_id)
                    if jobs:
                        client.display_jobs(jobs)
                        
                        select_job = Confirm.ask("Select a job to view logs?")
                        if select_job:
                            try:
                                job_id = Prompt.ask("Enter job ID")
                                current_job_id = int(job_id)
                                
                                with Progress(
                                    SpinnerColumn(),
                                    TextColumn("[bold blue]Fetching job logs..."),
                                    transient=True,
                                ) as progress:
                                    progress.add_task("logs", total=None)
                                    logs = client.get_job_logs(current_job_id)
                                
                                if logs:
                                    display_raw = Confirm.ask("Display raw logs with original formatting?")
                                    if display_raw:
                                        # Print raw logs with original ANSI formatting
                                        print(logs)
                                    else:
                                        # Just output to terminal without Rich syntax highlighting
                                        # This preserves GitLab's ANSI color codes
                                        print(f"\n--- Logs for Job #{current_job_id} ---")
                                        print(logs)
                                        print("-----------------------------")
                                else:
                                    console.print(f"[bold red]No logs found for job {current_job_id}[/bold red]")
                            except ValueError:
                                console.print("[bold red]Error: Job ID must be an integer[/bold red]")
                            except Exception as e:
                                console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    else:
                        console.print(f"[bold red]No jobs found for pipeline {current_pipeline_id}[/bold red]")
                except ValueError:
                    console.print("[bold red]Error: Pipeline ID must be an integer[/bold red]")
                except Exception as e:
                    console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    
            elif user_input.lower() == 'job-logs':
                try:
                    if current_job_id:
                        use_current = Confirm.ask(f"Use current job (ID: {current_job_id})?")
                        if not use_current:
                            job_id = Prompt.ask("Enter job ID")
                            current_job_id = int(job_id)
                    else:
                        job_id = Prompt.ask("Enter job ID")
                        current_job_id = int(job_id)
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]Fetching job logs..."),
                        transient=True,
                    ) as progress:
                        progress.add_task("logs", total=None)
                        logs = client.get_job_logs(current_job_id)
                    
                    if logs:
                        display_raw = Confirm.ask("Display raw logs with original formatting?")
                        if display_raw:
                            # Print raw logs with original ANSI formatting
                            print(logs)
                        else:
                            # Just output to terminal without Rich syntax highlighting
                            # This preserves GitLab's ANSI color codes
                            print(f"\n--- Logs for Job #{current_job_id} ---")
                            print(logs)
                            print("-----------------------------")
                    else:
                        console.print(f"[bold red]No logs found for job {current_job_id}[/bold red]")
                except ValueError:
                    console.print("[bold red]Error: Job ID must be an integer[/bold red]")
                except Exception as e:
                    console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    
            else:
                console.print(f"[bold red]Unknown command: {user_input}[/bold red]")
                console.print("Type 'help' to see available commands")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}[/bold red]")
    
    console.print("[bold blue]Goodbye![/bold blue]")

if __name__ == "__main__":
    app() 