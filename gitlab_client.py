import os
import sys
import yaml
import json
from typing import Dict, List, Optional, Any, Union
import gitlab
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

class GitLabClient:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize GitLab client with configuration."""
        self.config = self._load_config(config_path)
        self.gl = self._init_gitlab()
        self.project = self._get_project()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        paths = [
            config_path,
            './.gitlab-helper.yaml',
            os.path.expanduser('~/.gitlab-helper.yaml')
        ]
        
        for path in paths:
            if path and os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        config = yaml.safe_load(f)
                        return config
                except Exception as e:
                    console.print(f"[bold red]Error loading config from {path}: {str(e)}[/bold red]")
        
        console.print("[bold red]No valid configuration found. Please create a .gitlab-helper.yaml file.[/bold red]")
        sys.exit(1)
    
    def _init_gitlab(self) -> gitlab.Gitlab:
        """Initialize GitLab API client."""
        try:
            url = self.config['gitlab']['url']
            token = self.config['gitlab']['token']
            return gitlab.Gitlab(url=url, private_token=token)
        except Exception as e:
            console.print(f"[bold red]Failed to initialize GitLab client: {str(e)}[/bold red]")
            sys.exit(1)
    
    def _get_project(self) -> Any:
        """Get GitLab project by ID."""
        try:
            project_id = self.config['gitlab']['project_id']
            return self.gl.projects.get(project_id)
        except Exception as e:
            console.print(f"[bold red]Failed to get project: {str(e)}[/bold red]")
            sys.exit(1)
    
    def get_pipelines(self, limit: int = 10) -> List[Any]:
        """Get list of pipelines."""
        try:
            return list(self.project.pipelines.list(per_page=limit))
        except Exception as e:
            console.print(f"[bold red]Failed to get pipelines: {str(e)}[/bold red]")
            return []
    
    def get_pipeline(self, pipeline_id: int) -> Any:
        """Get specific pipeline by ID."""
        try:
            return self.project.pipelines.get(pipeline_id)
        except Exception as e:
            console.print(f"[bold red]Failed to get pipeline {pipeline_id}: {str(e)}[/bold red]")
            return None
    
    def get_latest_pipeline(self) -> Any:
        """Get the latest pipeline."""
        pipelines = self.get_pipelines(limit=1)
        return pipelines[0] if pipelines else None
    
    def create_pipeline(self, ref: str = 'main', variables: Optional[Dict[str, str]] = None) -> Any:
        """Create a new pipeline."""
        try:
            variables_list = None
            if variables:
                variables_list = [{'key': k, 'value': v} for k, v in variables.items()]
            
            pipeline = self.project.pipelines.create({'ref': ref, 'variables': variables_list})
            return pipeline
        except Exception as e:
            console.print(f"[bold red]Failed to create pipeline: {str(e)}[/bold red]")
            return None
    
    def get_jobs(self, pipeline_id: int) -> List[Any]:
        """Get jobs for a specific pipeline."""
        try:
            pipeline = self.get_pipeline(pipeline_id)
            if pipeline:
                return list(pipeline.jobs.list(all=True))
            return []
        except Exception as e:
            console.print(f"[bold red]Failed to get jobs for pipeline {pipeline_id}: {str(e)}[/bold red]")
            return []
    
    def get_job(self, job_id: int) -> Any:
        """Get specific job by ID."""
        try:
            # Ensure job_id is an integer
            job_id = int(job_id)
            return self.project.jobs.get(job_id)
        except ValueError:
            console.print(f"[bold red]Invalid job ID: {job_id}. Job ID must be an integer.[/bold red]")
            return None
        except Exception as e:
            console.print(f"[bold red]Failed to get job {job_id}: {str(e)}[/bold red]")
            return None
    
    def get_job_logs(self, job_id: int) -> str:
        """Get logs for a specific job."""
        try:
            # Ensure job_id is an integer
            job_id = int(job_id)
            job = self.get_job(job_id)
            if job:
                # Properly decode the bytes output to string
                # Use 'utf-8' with 'replace' error handler to handle invalid characters
                logs_bytes = job.trace()
                if isinstance(logs_bytes, bytes):
                    return logs_bytes.decode('utf-8', errors='replace')
                return logs_bytes
            return ""
        except ValueError:
            console.print(f"[bold red]Invalid job ID: {job_id}. Job ID must be an integer.[/bold red]")
            return ""
        except Exception as e:
            console.print(f"[bold red]Failed to get logs for job {job_id}: {str(e)}[/bold red]")
            return ""
    
    def display_pipelines(self, pipelines: List[Any]) -> None:
        """Display pipelines in a table format."""
        table = Table(title="GitLab Pipelines")
        
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Status", justify="left")
        table.add_column("Ref", justify="left")
        table.add_column("SHA", justify="left")
        table.add_column("Created At", justify="left")
        
        for pipeline in pipelines:
            status_style = self._get_status_style(pipeline.status)
            table.add_row(
                str(pipeline.id),
                f"[{status_style}]{pipeline.status}[/{status_style}]",
                pipeline.ref,
                pipeline.sha[:8],
                pipeline.created_at
            )
        
        console.print(table)
    
    def display_jobs(self, jobs: List[Any]) -> None:
        """Display jobs in a table format."""
        table = Table(title="Pipeline Jobs")
        
        table.add_column("Stage", justify="left")
        table.add_column("Job", justify="left")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Status", justify="left")
        
        for job in jobs:
            status_style = self._get_status_style(job.status)
            table.add_row(
                job.stage,
                job.name,
                str(job.id),
                f"[{status_style}]{job.status}[/{status_style}]"
            )
        
        console.print(table)
    
    def _get_status_style(self, status: str) -> str:
        """Get appropriate style for a status."""
        status_styles = {
            'success': 'green',
            'failed': 'red',
            'running': 'blue',
            'pending': 'yellow',
            'canceled': 'red',
            'skipped': 'grey',
            'created': 'cyan',
            'manual': 'magenta'
        }
        return status_styles.get(status, 'white') 