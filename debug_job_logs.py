#!/usr/bin/env python3

import sys
from gitlab_client import GitLabClient

def debug_job_logs(job_id, raw=True):
    """Debug function to fetch and print job logs."""
    client = GitLabClient()
    print(f"Fetching logs for job ID: {job_id}")
    
    # Get the job logs
    logs = client.get_job_logs(job_id)
    
    if logs:
        print(f"Successfully retrieved logs for job #{job_id}")
        
        if raw:
            # Print raw logs with original ANSI formatting
            print(f"\n--- Logs for Job #{job_id} ---")
            print(logs)
            print("-----------------------------")
        else:
            # Use rich for formatted display
            from rich.console import Console
            from rich.syntax import Syntax
            from rich.panel import Panel
            
            console = Console(color_system="auto")
            syntax = Syntax(logs, "bash", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title=f"Logs for Job #{job_id}", expand=False))
    else:
        print(f"No logs found for job {job_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        job_id = 9546659471  # Default job ID
    else:
        job_id = sys.argv[1]
    
    # You can set a breakpoint here for debugging in VSCode
    # import pdb; pdb.set_trace()
    
    # Set raw=True to see original GitLab formatting with ANSI colors
    debug_job_logs(job_id, raw=True) 