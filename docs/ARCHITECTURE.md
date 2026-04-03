# Architecture

## System Overview

```mermaid
graph TB
    subgraph "GitHub (labworksdev/todo-app)"
        REPO[Repository<br>main branch]
        PR[Pull Request]
        CI[CI Pipeline<br>.github/workflows/ci.yml]
        CD[Deploy Pipeline<br>.github/workflows/deploy.yml]
    end

    subgraph "Azure (rg-todo-app, East US)"
        ACR[Azure Container Registry<br>labworksacr.azurecr.io]
        
        subgraph "Container Apps Environment (cae-todo-app)"
            APP[Container App<br>todo-app<br>Python/Flask + Gunicorn]
            DB[(SQLite<br>todos.db)]
        end
        
        LOGS[Log Analytics<br>Workspace]
    end

    subgraph "Users"
        BROWSER[Web Browser]
        DEV[Developer<br>Student VM]
    end

    DEV -->|push branch| PR
    PR -->|triggers| CI
    CI -->|build + lint + test| CI
    PR -->|merge| REPO
    REPO -->|push to main| CD
    CD -->|build image| ACR
    CD -->|deploy| APP
    APP --- DB
    APP -.->|logs| LOGS
    BROWSER -->|HTTPS| APP
```

## Request Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant App as Container App<br>(Flask/Gunicorn)
    participant DB as SQLite

    User->>Browser: Open app URL
    Browser->>App: GET /
    App->>DB: SELECT * FROM todos
    DB-->>App: [todo rows]
    App-->>Browser: HTML page

    User->>Browser: Add a todo
    Browser->>App: POST /add (title=...)
    App->>DB: INSERT INTO todos
    App-->>Browser: 302 Redirect /
    Browser->>App: GET /
    App->>DB: SELECT * FROM todos
    DB-->>App: [updated rows]
    App-->>Browser: HTML page
```

## CI/CD Pipeline

```mermaid
graph LR
    subgraph "Pull Request"
        A[Push branch] --> B[CI: Checkout]
        B --> C[Install deps]
        C --> D[Lint with ruff]
        D --> E[Run tests]
        E --> F[Build Docker image]
        F --> G{All pass?}
        G -->|Yes| H[✅ Ready to merge]
        G -->|No| I[❌ Fix and repush]
    end

    subgraph "Merge to Main"
        J[Merge PR] --> K[CD: Checkout]
        K --> L[Azure Login]
        L --> M[ACR Login]
        M --> N[Build & Push Image]
        N --> O[Update Container App]
        O --> P[✅ Live in ~1 min]
    end

    H --> J
```

## Infrastructure (Terraform)

```mermaid
graph TB
    subgraph "infra/ (Terraform)"
        TF[terraform.tfvars<br>subscription, region, app name]
    end

    TF --> RG[Resource Group<br>rg-todo-app]
    RG --> ACR[Container Registry<br>labworksacr<br>Basic SKU]
    RG --> LOGS[Log Analytics<br>Workspace<br>30-day retention]
    RG --> ENV[Container Apps<br>Environment<br>cae-todo-app]
    LOGS --> ENV
    ENV --> APP[Container App<br>todo-app<br>0.5 CPU / 1GB RAM<br>1-3 replicas]
    ACR -.->|image source| APP
```

## Workshop Architecture (Full Picture)

```mermaid
graph TB
    subgraph "Student VMs (Azure, East US)"
        subgraph "VM: student-01"
            WIN1[Windows 11<br>VS Code + Claude Code ext]
            WSL1[WSL Ubuntu<br>Claude Code CLI]
        end
        subgraph "VM: student-02"
            WIN2[Windows 11]
            WSL2[WSL Ubuntu]
        end
        DOTS[... x10 students]
    end

    subgraph "Azure AI Foundry (Sweden Central)"
        CLAUDE[Claude Models<br>Opus 4.6 / Sonnet 4.6 / Haiku 4.5]
    end

    subgraph "GitHub"
        REPO[labworksdev/todo-app<br>PRs + CI/CD]
    end

    subgraph "Azure (East US)"
        LIVE[Container App<br>todo-app<br>Live deployment]
    end

    WIN1 & WSL1 -->|Claude Code| CLAUDE
    WIN2 & WSL2 -->|Claude Code| CLAUDE
    WIN1 & WSL1 -->|git push / PR| REPO
    WIN2 & WSL2 -->|git push / PR| REPO
    REPO -->|auto-deploy| LIVE
```

## Data Model (Current)

```mermaid
erDiagram
    TODOS {
        int id PK "AUTOINCREMENT"
        text title "NOT NULL"
        bool completed "DEFAULT 0"
        timestamp created_at "DEFAULT CURRENT_TIMESTAMP"
    }
```

## Future Data Model (Target)

```mermaid
erDiagram
    USERS {
        int id PK
        text username UK
        text password_hash
        text display_name
        text avatar_url
        timestamp created_at
    }

    PROJECTS {
        int id PK
        text name
        text description
        int owner_id FK
        timestamp created_at
    }

    SPRINTS {
        int id PK
        int project_id FK
        text name
        date start_date
        date end_date
        text status "planned|active|completed"
    }

    EPICS {
        int id PK
        int project_id FK
        text name
        text description
        text status "open|in_progress|done"
    }

    TODOS {
        int id PK
        text title
        text description
        bool completed
        text priority "high|medium|low"
        int story_points
        date due_date
        int assigned_to FK
        int project_id FK
        int sprint_id FK
        int epic_id FK
        int parent_id FK "subtasks"
        int position "sort order"
        timestamp created_at
        timestamp updated_at
    }

    COMMENTS {
        int id PK
        int todo_id FK
        int user_id FK
        text body
        timestamp created_at
    }

    TAGS {
        int id PK
        text name UK
        text color
    }

    TODO_TAGS {
        int todo_id FK
        int tag_id FK
    }

    ACTIVITY_LOG {
        int id PK
        int user_id FK
        int todo_id FK
        text action "created|updated|completed|commented"
        text details
        timestamp created_at
    }

    USERS ||--o{ TODOS : "assigned_to"
    USERS ||--o{ PROJECTS : "owns"
    USERS ||--o{ COMMENTS : "writes"
    USERS ||--o{ ACTIVITY_LOG : "performs"
    PROJECTS ||--o{ SPRINTS : "has"
    PROJECTS ||--o{ EPICS : "has"
    PROJECTS ||--o{ TODOS : "contains"
    SPRINTS ||--o{ TODOS : "includes"
    EPICS ||--o{ TODOS : "groups"
    TODOS ||--o{ TODOS : "subtasks"
    TODOS ||--o{ COMMENTS : "has"
    TODOS ||--o{ TODO_TAGS : "tagged"
    TAGS ||--o{ TODO_TAGS : "applied"
    TODOS ||--o{ ACTIVITY_LOG : "tracked"
```
