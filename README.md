# GitLab Job Helper

A command-line application for interacting with GitLab CI/CD pipelines.

## Features

- List specific pipelines
- Get latest pipeline
- Create new pipelines with variables
- Check pipeline status
- List jobs in a pipeline
- View job logs
- Interactive console mode

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Create a `.gitlab-helper.yaml` file in your home directory or the project directory:

```yaml
gitlab:
  url: "https://gitlab.com"  # Your GitLab instance URL
  project_id: "12345"        # Your GitLab project ID
  token: "your_token_here"   # Your GitLab API token
```

## Usage

### CLI Mode

```bash
# List pipelines
python gitlab_helper.py pipelines list

# Get the latest pipeline
python gitlab_helper.py pipelines latest

# Create a new pipeline
python gitlab_helper.py pipelines create

# Create a new pipeline with variables
python gitlab_helper.py pipelines create --variables '{"JOB_TYPE": "ABCD"}'

# Get pipeline status
python gitlab_helper.py pipelines status [PIPELINE_ID]

# List jobs in a pipeline
python gitlab_helper.py jobs list [PIPELINE_ID]

# Get job logs
python gitlab_helper.py jobs logs [JOB_ID]
```

### Interactive Mode

```bash
python gitlab_helper.py interactive
```

Then follow the on-screen prompts to navigate through different options. 