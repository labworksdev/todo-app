# Todo App

A simple Python/Flask to-do application for the PSEA Agentic Coding Workshop.

## Live App

**https://todo-app.happysmoke-64bbe2ef.eastus.azurecontainerapps.io/**

## Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/WSL
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open http://localhost:5000

## Docker

```bash
# Build and run locally
./scripts/dev-docker.sh

# Or manually:
docker build -t todo-app .
docker run -p 8000:8000 todo-app
```

Open http://localhost:8000

## Deploy to Azure

```bash
# Build image in ACR and update the live app
./scripts/deploy.sh
```

Requires Azure CLI logged in with access to the `rg-todo-app` resource group.

## Project Structure

```
├── app.py                  # Flask application
├── templates/
│   └── index.html          # HTML template
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container image
├── scripts/
│   ├── deploy.sh           # Deploy to Azure Container Apps
│   └── dev-docker.sh       # Run locally with Docker
├── docs/
│   └── WORKSHOP-FEATURES.md  # Full feature backlog
└── README.md
```

## Workshop

See [docs/WORKSHOP-FEATURES.md](docs/WORKSHOP-FEATURES.md) for the full feature backlog.

This app starts as a bare-bones ugly todo list. Your mission: use agentic coding to evolve it into a polished agile project management tool.
