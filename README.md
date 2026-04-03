# Todo App

A simple Python/Flask to-do application for the PSEA Agentic Coding Workshop.

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
# Build
docker build -t todo-app .

# Run
docker run -p 8000:8000 todo-app
```

Open http://localhost:8000

## Project Structure

```
├── app.py              # Flask application
├── templates/
│   └── index.html      # HTML template
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image
└── README.md
```

## Workshop Exercises

This is the starter app. During the workshop, you'll use Claude Code to:

1. **Add features** — due dates, priorities, categories
2. **Improve the UI** — better styling, responsive design, dark mode
3. **Add an API** — REST endpoints for the todo operations
4. **Write tests** — unit tests and integration tests
5. **Deploy to Azure** — containerize and deploy to Azure Web Apps
