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

## CI/CD Pipeline

Deployment is fully automated via GitHub Actions:

- **On pull request** → builds, lints, runs tests (`.github/workflows/ci.yml`)
- **On merge to main** → builds Docker image, pushes to ACR, deploys to Azure Container Apps (`.github/workflows/deploy.yml`)

No manual deploy needed. Merge a PR and the live app updates in ~1 minute.

### Manual Deploy (if needed)

```bash
./scripts/deploy.sh
```

## Infrastructure

All Azure infrastructure is defined in Terraform under `infra/`.

```bash
cd infra
terraform init
terraform plan
terraform apply
```

Resources created:
- **Resource Group** (`rg-todo-app`)
- **Azure Container Registry** (`labworksacr`)
- **Container Apps Environment** (`cae-todo-app`)
- **Container App** (`todo-app`) — public HTTPS endpoint
- **Log Analytics Workspace** — for logs and monitoring

Teardown: `terraform destroy`

## Project Structure

```
├── app.py                    # Flask application
├── templates/
│   └── index.html            # HTML template
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image
├── infra/                    # Terraform infrastructure
│   ├── main.tf               # ACR, Container Apps, networking
│   ├── variables.tf          # Configurable inputs
│   ├── outputs.tf            # App URL, ACR details
│   └── terraform.tfvars      # Environment values
├── .github/workflows/
│   ├── ci.yml                # PR validation (build + test)
│   └── deploy.yml            # Auto-deploy on merge to main
├── scripts/
│   ├── deploy.sh             # Manual deploy to Azure
│   └── dev-docker.sh         # Run locally with Docker
├── docs/
│   └── WORKSHOP-FEATURES.md  # Full feature backlog
└── README.md
```

## Workshop

See [docs/WORKSHOP-FEATURES.md](docs/WORKSHOP-FEATURES.md) for the full feature backlog.

This app starts as a bare-bones ugly todo list. Your mission: use agentic coding to evolve it into a polished agile project management tool.
