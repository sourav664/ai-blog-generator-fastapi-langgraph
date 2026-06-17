# 🤖 AI Blog Generator

> **Autonomously research, write, illustrate, and publish long-form technical blogs — powered by LangGraph multi-agent workflows, OpenAI, and FastAPI.**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-FF6F61?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Google Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Database Design](#-database-design)
- [Neon Database Architecture](#-neon-database-architecture)
- [Authentication Flow](#-authentication-flow)
- [AI Blog Generation Workflow](#-ai-blog-generation-workflow)
- [API Documentation](#-api-documentation)
- [Environment Variables](#-environment-variables)
- [Local Development Setup](#-local-development-setup)
- [Docker Setup](#-docker-setup)
- [Database Migrations](#-database-migrations)
- [Testing](#-testing)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Google Cloud Deployment](#-google-cloud-deployment)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Performance Optimization](#-performance-optimization)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

### The Problem

Creating high-quality, long-form technical blog content requires hours of research, writing, editing, and sourcing relevant illustrations. Content teams, developers, and technical writers face a constant bottleneck: turning an idea into a publication-ready article takes days, not minutes.

### The Solution

**AI Blog Generator** is a production-grade, API-first platform that collapses the blog creation pipeline into a single API call. A user submits a topic; the system autonomously:

1. **Routes** the request — deciding whether the topic needs live web research or can be answered from model knowledge alone
2. **Researches** the topic using Tavily Search for up-to-date evidence
3. **Plans** a structured blog outline using an Orchestrator agent
4. **Writes** each section in parallel using worker agents (fan-out pattern via LangGraph's `Send` API)
5. **Generates** contextually relevant images using OpenAI's `gpt-image-2` model
6. **Assembles** the full Markdown document with embedded images
7. **Persists** the blog and images in PostgreSQL
8. **Exposes** publishing, editing, and liking through a REST API and a Jinja2-powered web UI

### Business Use Cases

| Use Case | Description |
|---|---|
| **Content Marketing** | Generate 1,500–5,000 word technical blogs at scale |
| **Developer Advocacy** | Auto-draft announcement posts, tutorials, and explainers |
| **News Roundups** | Research and summarize the latest developments in any field |
| **Internal Knowledge Bases** | Generate evergreen technical documentation |
| **SaaS Blogging Platforms** | Embed AI generation into any existing CMS or blog platform |

### Target Users

- Individual developers who want to publish technical blogs without spending hours writing
- Content marketing teams at tech companies
- Developer relations and advocacy teams
- SaaS platforms that want to embed AI-powered content generation

---

## ✨ Features

### 🔐 User & Authentication Features

- **Registration** — Email + username-based account creation with full uniqueness validation (case-insensitive)
- **JWT Login** — OAuth2 password flow returning Bearer tokens (HS256, configurable expiry)
- **Token-Based Auth** — Stateless JWT authentication across all protected endpoints
- **Forgot Password** — Secure token generation (URL-safe, SHA-256 hashed) with email delivery via async SMTP
- **Password Reset** — Time-limited (60 minutes) token-based password reset workflow
- **Change Password** — Authenticated in-session password update with immediate token invalidation
- **Profile Management** — Update username and email with duplicate detection
- **Profile Picture** — Upload (JPEG/PNG/GIF/WebP) with auto-resize to 300×300 via Pillow, stored in AWS S3
- **Delete Account** — Cascading delete of all user data including profile images from S3

### 🤖 AI & Multi-Agent Features

- **Intelligent Router** — Classifies topics as `closed_book`, `hybrid`, or `open_book` to determine research needs
- **Tavily Web Research** — Fetches up to 6 results per query across multiple search queries for current-events topics
- **Evidence Synthesis** — Deduplicates and structures Tavily results into a typed `EvidencePack` using LLM structured output
- **Blog Planner (Orchestrator)** — Generates a typed `Plan` with 5–9 structured sections, each with goals, bullets, word targets, and metadata flags
- **Parallel Section Writers** — Fan-out worker agents write each blog section concurrently using LangGraph's `Send` API
- **Image Decision Agent** — Analyzes the merged blog to determine where images add value, generates prompts, and inserts `[[IMAGE_N]]` placeholders
- **Image Generation** — Generates images via OpenAI `gpt-image-2` (or Google Gemini) with exponential backoff retry logic
- **Multi-Provider LLM Support** — Switchable between OpenAI (GPT-4o), Google (Gemini 2.5 Flash), and Groq via YAML configuration
- **Jinja2 Prompt Templates** — All system prompts are Jinja2 templates with conditional rendering for dynamic context injection

### 📝 Blog Features

- **AI Blog Generation** — One-endpoint full blog pipeline (topic → published-ready Markdown)
- **Draft Management** — Blogs default to unpublished (`is_published=False`) for review before going live
- **Publishing Control** — Owner-only publish action to make blogs publicly visible
- **Blog Editing** — Update title and content of any owned blog via `PUT` request
- **Blog Deletion** — Owner-only cascading delete (including associated `BlogImage` records)
- **Blog Likes** — Unauthenticated like counter with atomic increment
- **Paginated Listings** — Both personal (`/api/blogs`) and public (`/api/blogs/published`) feeds with cursor-based pagination (`skip`/`limit`)
- **Image Storage** — Blog images stored as binary blobs in `blog_images` table; served via `/images/{filename}` with static file fallback
- **Markdown Rendering** — Jinja2 templates render Markdown blog content in the web UI

### 🌐 Web UI Features

- **Home Page** — Paginated feed of all published blogs
- **Blog Detail Page** — Full blog post rendering with author info
- **User Posts Page** — All published blogs from a specific author
- **Login / Register Pages** — Server-side rendered authentication forms
- **Dashboard** — Authenticated user dashboard
- **Account Management** — Profile and password management pages
- **Password Reset Flow** — Forgot password and reset password pages
- **Error Pages** — Custom 404/422/500 error pages with templated responses
- **Security Headers** — Middleware automatically adds `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, and `Referrer-Policy`

### ⚙️ Infrastructure Features

- **Multi-Stage Docker Build** — `python:3.14-slim-bookworm` builder + production stage with non-root user
- **UV Package Manager** — Fast, locked dependency installation with bytecode compilation
- **Alembic Migrations** — Auto-generate + async migration runner using `MIGRATION_DATABASE_URL` (non-pooled)
- **Async Database Engine** — `create_async_engine` with `pool_pre_ping=True` and `pool_recycle=300`
- **Google Cloud Run** — Managed serverless deployment, `asia-south1` region, 2 vCPU / 2 GiB RAM
- **Artifact Registry** — Docker images stored in `asia-south1-docker.pkg.dev`
- **Secret Manager Integration** — Production secrets mounted at `/secrets/app/.env` inside the container
- **OIDC / Workload Identity Federation** — Keyless GitHub Actions → GCP authentication
- **Structured JSON Logging** — `structlog` with ISO timestamps, log level tagging, and file + console output
- **Health Check Endpoint** — `/health` endpoint with live database connectivity probe

---

## 🏗 System Architecture

### High-Level Architecture
```mermaid
flowchart TD
    U[User / Browser] --> FE[Jinja2 Web UI]
    U --> API[FastAPI REST API]

    FE --> API

    API --> AUTH[JWT Authentication]
    AUTH --> ROUTER[API Routers]

    ROUTER --> DB[(Neon PostgreSQL)]
    ROUTER --> WF[LangGraph Blog Generator]

    WF --> TAV[Tavily Search API]
    WF --> LLM[OpenAI GPT-4o]
    WF --> IMG[OpenAI Image Generator]

    WF --> DB

    API --> S3[AWS S3 Profile Images]

    style U fill:#6C63FF,color:#fff
    style API fill:#009688,color:#fff
    style WF fill:#FF6F61,color:#fff
    style DB fill:#336791,color:#fff
    style S3 fill:#FF9900,color:#fff
```

### Infrastructure Architecture

```mermaid
flowchart TD
    DEV([👨‍💻 Developer]) -->|git push| GH[GitHub Repository]
    GH --> GHA[GitHub Actions CI/CD]
    GHA --> TEST[🧪 Run Pytest Suite\nuv run pytest]
    TEST --> BUILD[🐳 Build Docker Image\ngpt-image-2 + FastAPI]
    BUILD --> AR[📦 Artifact Registry\nasia-south1-docker.pkg.dev]
    AR --> CR[☁️ Cloud Run Service\n2 vCPU · 2 GiB · 0-10 instances]
    CR --> SM[🔐 Secret Manager\n/secrets/app/.env]
    CR --> DB[(🐘 Neon PostgreSQL\nServerless + Pooled)]
    CR --> S3[(🪣 AWS S3\nProfile Pictures)]

    style GHA fill:#2088FF,color:#fff
    style CR fill:#4285F4,color:#fff
    style DB fill:#336791,color:#fff
    style SM fill:#EA4335,color:#fff
    style AR fill:#34A853,color:#fff
```

### AI Workflow Architecture

```mermaid
flowchart TD
    A([📝 User Submits Topic]) --> B[Router Agent\nClassify: closed_book / hybrid / open_book]
    B -->|needs_research = true| C[Research Agent\nGenerate search queries]
    B -->|needs_research = false| E
    C --> D[🔍 Tavily Search\nFetch + deduplicate evidence]
    D --> E[Orchestrator Agent\nGenerate structured Plan\n5–9 sections with metadata]
    E --> F[⚡ Fan-Out via LangGraph Send API\nSpawn parallel Worker Agents]
    F --> G1[Worker 1\nWrite Section 1]
    F --> G2[Worker 2\nWrite Section 2]
    F --> GN[Worker N\nWrite Section N]
    G1 & G2 & GN --> H[Reducer: Merge Sections\nAssemble full Markdown]
    H --> I[Image Decision Agent\nInsert IMAGE placeholders\nGenerate prompts]
    I --> J[Image Generator\nOpenAI gpt-image-2\nwith retry + backoff]
    J --> K[Final Assembly\nReplace placeholders with real images]
    K --> L[(PostgreSQL\nPersist blog + images)]

    style A fill:#6C63FF,color:#fff
    style E fill:#FF6F61,color:#fff
    style F fill:#FF9900,color:#fff
    style J fill:#412991,color:#fff
    style L fill:#336791,color:#fff
```

---

## 🛠 Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Web Framework** | FastAPI | ≥ 0.135 | Async REST API + Jinja2 web UI |
| **Language** | Python | 3.13 | Core runtime |
| **ASGI Server** | Uvicorn | (via FastAPI[standard]) | Production ASGI server |
| **AI Orchestration** | LangGraph | ≥ 1.1.9 | Multi-agent stateful workflow graph |
| **LLM (Text)** | LangChain OpenAI | ≥ 1.2.0 | GPT-4o for planning, research, writing |
| **LLM (Text)** | LangChain Google Genai | ≥ 4.2.2 | Gemini 2.5 Flash (optional provider) |
| **LLM (Text)** | LangChain Groq | ≥ 1.1.2 | Groq / DeepSeek (optional provider) |
| **Image Generation** | OpenAI | ≥ 2.32.0 | gpt-image-2 via b64_json |
| **Web Research** | LangChain Tavily | ≥ 0.2.18 | Real-time web search for evidence |
| **Prompt Templates** | Jinja2 | ≥ 3.1.6 | Dynamic system prompt rendering |
| **ORM** | SQLAlchemy | ≥ 2.0.49 | Async ORM with `mapped_column` |
| **Database** | PostgreSQL (Neon) | — | Serverless, autoscaling PostgreSQL |
| **DB Driver** | Psycopg (v3) | ≥ 3.3.3 | Async PostgreSQL binary driver |
| **Migrations** | Alembic | ≥ 1.18.4 | Schema versioning and migration |
| **Validation** | Pydantic v2 | ≥ 2.12.5 | Request/response validation + settings |
| **Settings** | Pydantic Settings | ≥ 2.14.0 | Env-file based configuration |
| **Auth** | PyJWT | ≥ 2.13.0 | HS256 JWT creation and validation |
| **Password Hashing** | pwdlib[argon2] | ≥ 0.3.0 | Argon2 password hashing |
| **Email** | aiosmtplib | ≥ 5.1.0 | Async SMTP email delivery |
| **Image Processing** | Pillow | ≥ 12.2.0 | Profile picture resizing + format conversion |
| **S3 Storage** | boto3 | ≥ 1.43.9 | AWS S3 profile image storage |
| **Logging** | structlog | ≥ 25.5.0 | Structured JSON logging |
| **Containerization** | Docker | — | Multi-stage production image |
| **Package Manager** | UV (Astral) | 0.11.6 | Fast locked dependency installation |
| **CI/CD** | GitHub Actions | — | Automated test + build + deploy |
| **Cloud Compute** | Google Cloud Run | — | Serverless managed container runtime |
| **Image Registry** | Google Artifact Registry | — | Docker image storage |
| **Secrets** | Google Secret Manager | — | Production secret injection |
| **Auth (CI)** | Workload Identity Federation | — | Keyless GitHub → GCP OIDC auth |
| **Testing** | Pytest + anyio | ≥ 9.0.3 | Async test suite |
| **Test Mocking** | moto[s3] | ≥ 5.2.1 | Mock AWS S3 in tests |

---

## 📁 Project Structure

```text
fastapi_blog_generator/
│
├── src/                          # Application source code
│   ├── main.py                   # FastAPI app factory, middleware, lifespan, UI routes
│   ├── auth.py                   # JWT creation, verification, password hashing, CurrentUser dep
│   ├── email_utils.py            # Async SMTP email sending, password reset email builder
│   ├── image_utils.py            # Pillow image processing, S3 upload/delete helpers
│   ├── check_s3.py               # S3 bucket connectivity check utility
│   ├── migrate_images.py         # One-time utility to migrate disk images to DB
│   ├── populate_db.py            # Database seeding script for development
│   └── routers/
│       ├── users.py              # User CRUD, auth, password reset, profile picture endpoints
│       └── blogs.py              # Blog generation, publish, update, delete, like, list endpoints
│
├── workflows/                    # LangGraph AI workflows
│   ├── blog_generator_workflow.py # Main blog generation graph (router → research → orch → workers)
│   └── image_workflow.py         # Image sub-graph (merge → decide_images → generate_and_place)
│
├── schemas/                      # Pydantic models and SQLAlchemy ORM models
│   ├── models.py                 # SQLAlchemy models (User, PasswordResetToken, GeneratedBlog, BlogImage)
│   │                             # + Pydantic AI models (Plan, Task, State, EvidenceItem, ImageSpec...)
│   └── schemas.py                # API request/response Pydantic schemas (UserCreate, Token, BlogResponse...)
│
├── config/
│   ├── config.py                 # Pydantic Settings class — loads from .env or /secrets/app/.env
│   └── configuration.yaml        # LLM provider config (provider, model, temperature, image quality)
│
├── database/
│   ├── database.py               # Async engine, session factory, Base, get_db, get_session_maker
│   └── __init__.py               # Re-exports engine, Base, get_db, get_session_maker, AsyncSessionLocal
│
├── prompt_library/
│   └── prompt_locator.py         # All Jinja2 system prompts:
│                                 #   ROUTER_SYSTEM_PROMPT, RESEARCH_SYSTEM_PROMPT,
│                                 #   ORCH_SYSTEM_PROMPT, WORKER_SYSTEM_PROMPT,
│                                 #   DECIDE_IMAGES_SYSTEM_PROMPT
│
├── utils/
│   ├── model_loader.py           # ModelLoader — loads LLM + image model from config; ApiKeyManager
│   └── config_loader.py          # YAML config loader with env override (CONFIG_PATH)
│
├── exception/
│   └── custom_exception.py       # BlogGeneratorException — captures file, line, traceback
│
├── logger/
│   ├── custom_logger.py          # CustomLogger — structlog with JSON output to file + console
│   └── __init__.py               # Exports GLOBAL_LOGGER singleton
│
├── alembic/                      # Database migration infrastructure
│   ├── env.py                    # Async migration runner using MIGRATION_DATABASE_URL
│   ├── script.py.mako            # Migration script template
│   └── versions/                 # 17 migration revision files
│
├── tests/
│   ├── conftest.py               # Pytest fixtures: async engine, db_session, client, mocked_aws
│   ├── test_users.py             # User endpoint tests (register, login, upload, forgot-password)
│   └── test_blogs.py             # Blog endpoint tests (generate, publish, update, delete, like, list)
│
├── templates/                    # Jinja2 HTML templates (home, post, login, register, dashboard...)
├── static/                       # Static assets (CSS, JS, default profile pic)
├── generated_blogs/              # Local Markdown output from workflow (development only)
├── images/                       # Transient image staging directory (cleared after DB write)
├── logs/                         # Structlog JSON log files (timestamped per run)
├── notebooks/                    # Jupyter notebooks for experimentation
│
├── Dockerfile                    # Multi-stage build: builder (UV) → production (non-root)
├── pyproject.toml                # Project metadata, dependencies, UV dev group
├── uv.lock                       # Locked dependency tree
├── alembic.ini                   # Alembic configuration
├── .env                          # Local development environment variables
├── .env.production               # Production environment variable template
├── .dockerignore                 # Files excluded from Docker build context
├── .gitignore                    # Git exclusions
├── .python-version               # Pinned Python version (3.13)
└── .github/
    └── workflows/
        └── ci-cd.yaml            # GitHub Actions: test → build → push → deploy
```

---

## 🗄 Database Design

### Entity Relationship Diagram

```mermaid
erDiagram
    users {
        int id PK
        string username "unique, max 50"
        string email "unique, max 120, lowercase"
        string password_hash "Argon2 hashed"
        string image_file "nullable, S3 filename"
    }

    password_reset_tokens {
        int id PK
        int user_id FK
        string token_hash "SHA-256 of URL-safe token, unique"
        datetime expires_at "UTC, 60-minute TTL"
        datetime created_at "UTC auto"
    }

    generated_blogs {
        int id PK
        string blog_id "UUID, unique index"
        string title "max 200"
        text content "Full Markdown content"
        text images "JSON array of image filenames"
        int user_id FK
        datetime created_at "UTC auto"
        bool is_published "default false"
        int likes "default 0"
    }

    blog_images {
        int id PK
        string blog_id FK "nullable, CASCADE delete"
        string filename "unique index"
        bytes data "LargeBinary — raw image bytes"
        string content_type "e.g. image/png"
    }

    users ||--o{ password_reset_tokens : "has"
    users ||--o{ generated_blogs : "authors"
    generated_blogs ||--o{ blog_images : "has"
```

### Entity Descriptions

#### `users`

The core identity table. Stores credentials, profile information, and the S3 filename of the profile picture (not the full URL — the URL is computed by the `image_path` property at runtime using the configured S3 bucket and region).

**Key design decisions:**
- Email stored lowercase for case-insensitive uniqueness enforcement
- Password stored as Argon2 hash via `pwdlib`
- Profile image managed externally in S3; only filename is stored
- Cascade deletes propagate to `password_reset_tokens` and `generated_blogs`

#### `password_reset_tokens`

Ephemeral token store for the password reset flow. Only the SHA-256 hash of the original URL-safe token is stored — the raw token is sent to the user's email and never persisted.

**Key design decisions:**
- One token per user enforced by deleting existing tokens before issuing a new one
- `expires_at` enforced at application level (not DB-level TTL)
- Token invalidated on successful reset by deleting all tokens for the user

#### `generated_blogs`

The primary content table. Stores the AI-generated blog as raw Markdown in `content`. The `images` column stores a JSON array of image filenames, and the `blog_id` UUID is used as the public identifier across the REST API.

**Key computed properties (on the ORM model):**
- `content_without_title` — strips the leading `# H1` from content for template display
- `parsed_images` — deserializes the `images` JSON string to a Python list
- `description` — first 300 characters of content, stripped of Markdown syntax, for previews

#### `blog_images`

Binary image storage. Images generated by the AI workflow are saved to disk temporarily, then read and inserted as `LargeBinary` rows. Images are served via the `/images/{filename}` endpoint, which reads directly from the database. This eliminates the need for a persistent filesystem in the Cloud Run environment.

---

## 🐘 Neon Database Architecture

```mermaid
flowchart TD
    CR[Cloud Run Container] -->|Pooled Connection\nDATABASE_URL| POOL[Neon Connection Pooler\nPgBouncer]
    POOL --> NEON[(Neon PostgreSQL\nServerless Branch)]
    ALB[Alembic Migration Job\nCloud Run Job] -->|Direct Connection\nMIGRATION_DATABASE_URL| NEON
    TEST[GitHub Actions\nPytest] -->|TEST_DATABASE_URL\nblog_test database| NEON

    style CR fill:#4285F4,color:#fff
    style POOL fill:#00BCD4,color:#fff
    style NEON fill:#336791,color:#fff
    style ALB fill:#FF6F61,color:#fff
```

### Why Neon PostgreSQL?

| Feature | Benefit |
|---|---|
| **Serverless** | No idle compute cost — scales to zero when not in use |
| **Auto-scaling** | Handles traffic spikes without manual intervention |
| **Connection Pooling** | Built-in PgBouncer pooler endpoint reduces connection overhead |
| **Branching** | Database branches for staging/preview environments |
| **SSL Required** | All connections enforce TLS (`sslmode=require`) |
| **Async Compatible** | Works natively with `psycopg` v3 async driver |

### Two Database URLs — Why?

Neon uses two different endpoints for different use cases:

| Variable | Endpoint Type | Used By | Why |
|---|---|---|---|
| `DATABASE_URL` | **Pooled** (PgBouncer) | FastAPI application | High concurrency, efficient connection reuse |
| `MIGRATION_DATABASE_URL` | **Direct** (non-pooled) | Alembic migrations | Migrations require a persistent session; pooling breaks `ALTER TABLE` |
| `TEST_DATABASE_URL` | **Direct** | Pytest suite | Isolated `blog_test` database for CI |

### SQLAlchemy Async Engine Configuration

```python
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,    # Detects stale connections before use
    pool_recycle=300,      # Recycles connections every 5 minutes
)
```

`pool_pre_ping=True` is critical for Neon because the serverless compute may be cold, and connections can appear stale after a period of inactivity.

### Alembic Async Migration Strategy

Alembic's `env.py` uses `async_engine_from_config` with `NullPool` to run migrations asynchronously. The `MIGRATION_DATABASE_URL` bypasses the PgBouncer pooler to ensure DDL statements execute in a dedicated, persistent session.

---

## 🔐 Authentication Flow

### Registration & Login

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as PostgreSQL

    C->>API: POST /api/users {username, email, password}
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: None (no duplicate)
    API->>API: hash_password(password) → Argon2 hash
    API->>DB: INSERT INTO users ...
    DB-->>API: new user row
    API-->>C: 201 UserPrivate {id, username, email, image_path}

    C->>API: POST /api/users/token {username=email, password}
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: user row
    API->>API: verify_password(plain, hash)
    API->>API: create_access_token({sub: user.id}, exp=30min)
    API-->>C: 200 {access_token, token_type: "bearer"}
```

### JWT Validation (Protected Endpoints)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant AUTH as Auth Module
    participant DB as PostgreSQL

    C->>API: GET /api/users/me\nAuthorization: Bearer <token>
    API->>AUTH: verify_access_token(token)
    AUTH->>AUTH: jwt.decode(token, secret_key, HS256)
    AUTH-->>API: user_id (sub claim)
    API->>DB: SELECT user WHERE id = user_id
    DB-->>API: User object
    API-->>C: 200 UserPrivate
```

### Password Reset Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant DB as PostgreSQL
    participant SMTP as SMTP Server

    U->>API: POST /api/users/forgot-password {email}
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: user (or None)
    API->>DB: DELETE existing reset tokens for user
    API->>API: token = secrets.token_urlsafe(32)
    API->>API: token_hash = sha256(token)
    API->>DB: INSERT password_reset_tokens {user_id, token_hash, expires_at=now+60min}
    API->>SMTP: send_password_reset_email(email, username, token) [BackgroundTask]
    API-->>U: 202 Accepted (always, even if email not found)

    U->>API: POST /api/users/reset-password {token, new_password}
    API->>API: token_hash = sha256(token)
    API->>DB: SELECT reset_token WHERE token_hash = ?
    DB-->>API: reset_token
    API->>API: check expires_at > now(UTC)
    API->>DB: UPDATE user.password_hash = argon2(new_password)
    API->>DB: DELETE all reset tokens for user
    API-->>U: 200 "Password reset successfully"
```

**Security note:** The `/api/users/forgot-password` endpoint always returns `202 Accepted` regardless of whether the email exists, preventing user enumeration attacks.

---

## 🤖 AI Blog Generation Workflow

The AI workflow is implemented as a **compiled LangGraph `StateGraph`** with typed state (`State: TypedDict`), persistent memory checkpointing (`MemorySaver`), and a sub-graph for image processing.

### The LangGraph Graph

```mermaid
flowchart LR
    START --> router
    router -->|needs_research=true| research
    router -->|needs_research=false| orchestrator
    research --> orchestrator
    orchestrator -->|Send API fan-out| worker
    worker --> reducer
    subgraph reducer ["reducer (sub-graph)"]
        merge_content --> decide_images
        decide_images --> generate_and_place_images
    end
    reducer --> END
```

### Step-by-Step Breakdown

#### Step 1 — Router Node (`_router_node`)

The LLM (GPT-4o) is invoked with `with_structured_output(RouterDecision)` to classify the topic.

```python
class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: List[str]   # only populated when needs_research=True
```

- `closed_book`: Evergreen topics (algorithms, data structures, core concepts) — no web research needed
- `hybrid`: Mostly evergreen but benefits from current tool references
- `open_book`: Time-sensitive topics (news, rankings, latest releases) — must use Tavily

#### Step 2 — Research Node (`_research_node`)

If `needs_research=True`, Tavily is called for each generated query (up to 6 results per query). Raw results are deduplicated by URL and synthesized by the LLM into a typed `EvidencePack`:

```python
class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str]
    snippet: Optional[str]
    source: Optional[str]
```

#### Step 3 — Orchestrator Node (`_orchestrator_node`)

The LLM generates a typed `Plan` with `with_structured_output(Plan)`, incorporating evidence from the research step:

```python
class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"]
    constraints: List[str]
    tasks: List[Task]   # 5–9 sections

class Task(BaseModel):
    id: int
    title: str
    goal: str                    # single sentence
    bullets: List[str]           # 3–6 concrete subpoints
    target_words: int            # 120–550
    requires_research: bool
    requires_citations: bool
    requires_code: bool
```

#### Step 4 — Fan-Out Workers (`_fanout` + `_worker_node`)

LangGraph's `Send` API spawns one `worker` node per `Task` in the plan — all executing in parallel. Each worker receives its `Task`, the full `Plan` context, and the evidence pack. It calls the LLM to write its section as Markdown, returning `(task_id, section_md)`.

The LangGraph state uses an `operator.add` reducer on the `sections` list to collect all worker results without race conditions:

```python
sections: Annotated[List[tuple[int, str]], operator.add]
```

#### Step 5 — Reducer Sub-Graph (Image Workflow)

The `MergeImagesWorker` sub-graph executes three sequential steps:

**`merge_content`**: Sorts sections by `task_id`, assembles the full `# Blog Title\n\n{body}` Markdown.

**`decide_images`**: The LLM analyzes the merged Markdown with `with_structured_output(GlobalImagePlan)` to decide:
- How many images are needed (0–5, based on content complexity)
- Where to insert `[[IMAGE_N]]` placeholders
- What to generate for each image (alt text, caption, prompt, size, quality)

**`generate_and_place_images`**: For each `ImageSpec`:
1. Calls `_generate_image_bytes(prompt)` → OpenAI `images.generate()` → decodes `b64_json` → raw bytes
2. Writes bytes to `images/` directory
3. Replaces `[[IMAGE_N]]` placeholder with `![alt](/images/filename)\n*caption*`
4. Falls back gracefully if generation fails (logs error, uses blockquote placeholder)

#### Step 6 — Database Persistence (in `blogs.py`)

The endpoint handles persistence with a carefully designed transaction pattern to avoid holding a DB connection open during the long LLM workflow:

1. **Release connection** — `await db.rollback(); await db.close()` before calling `generate_blog`
2. **Run workflow** — `await run_in_threadpool(generate_blog, topic)` (LangGraph is synchronous)
3. **Pre-read images from disk** — Read all image bytes into memory before opening a DB session
4. **Rapid DB write** — Open a fresh session, insert `GeneratedBlog` + all `BlogImage` rows in a single transaction
5. **Cleanup** — Delete image files from disk after successful commit

---

## 📡 API Documentation

> Interactive docs available at: `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`

### Users API (`/api/users`)

| Method | Route | Auth | Description |
|---|---|---|---|
| `POST` | `/api/users` | ❌ Public | Register a new user |
| `POST` | `/api/users/token` | ❌ Public | Login and obtain JWT token |
| `GET` | `/api/users/me` | ✅ Bearer | Get current authenticated user |
| `GET` | `/api/users/{user_id}` | ❌ Public | Get public user profile |
| `PATCH` | `/api/users/{user_id}` | ✅ Bearer (owner) | Update username / email |
| `DELETE` | `/api/users/{user_id}` | ✅ Bearer (owner) | Delete account and all data |
| `PATCH` | `/api/users/{user_id}/picture` | ✅ Bearer (owner) | Upload profile picture to S3 |
| `DELETE` | `/api/users/{user_id}/picture` | ✅ Bearer (owner) | Remove profile picture from S3 |
| `GET` | `/api/users/{user_id}/posts` | ❌ Public | Paginated list of user's blogs |
| `POST` | `/api/users/forgot-password` | ❌ Public | Send password reset email |
| `POST` | `/api/users/reset-password` | ❌ Public | Reset password with token |
| `PATCH` | `/api/users/me/password` | ✅ Bearer | Change password (authenticated) |

#### POST `/api/users` — Register

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response `201`:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "image_file": null,
  "image_path": "/static/profile_pics/default.jpg"
}
```

#### POST `/api/users/token` — Login

**Request (form-encoded):**
```
username=john@example.com&password=securepassword123
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST `/api/users/forgot-password`

**Request:**
```json
{ "email": "john@example.com" }
```

**Response `202`:**
```json
{
  "message": "If an account exists with this email, you will receive password reset instructions."
}
```

---

### Blogs API (`/api/blogs`)

| Method | Route | Auth | Description |
|---|---|---|---|
| `POST` | `/api/blogs/generate` | ✅ Bearer | Generate a new AI blog from a topic |
| `GET` | `/api/blogs` | ✅ Bearer | List all blogs for current user (paginated) |
| `GET` | `/api/blogs/published` | ❌ Public | List all published blogs (paginated) |
| `POST` | `/api/blogs/{blog_id}/publish` | ✅ Bearer (owner) | Publish a draft blog |
| `PUT` | `/api/blogs/{blog_id}` | ✅ Bearer (owner) | Update blog title or content |
| `DELETE` | `/api/blogs/{blog_id}` | ✅ Bearer (owner) | Delete a blog |
| `POST` | `/api/blogs/{blog_id}/like` | ❌ Public | Increment like count |

#### POST `/api/blogs/generate` — Generate Blog

**Request:**
```json
{ "topic": "How Transformer Attention Mechanisms Work" }
```

**Response `201`:**
```json
{
  "id": 42,
  "blog_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "How Transformer Attention Mechanisms Work",
  "content": "# How Transformer Attention Mechanisms Work\n\n## Introduction\n...",
  "images": "[\"qkv_flow.png\", \"attention_matrix.png\"]",
  "user_id": 1,
  "created_at": "2026-06-17T09:00:00Z",
  "is_published": false,
  "likes": 0,
  "author": {
    "id": 1,
    "username": "johndoe",
    "image_file": null,
    "image_path": "/static/profile_pics/default.jpg"
  },
  "description": "Transformers have revolutionized NLP and beyond...",
  "content_without_title": "## Introduction\n\nTransformers...",
  "parsed_images": ["qkv_flow.png", "attention_matrix.png"]
}
```

#### GET `/api/blogs/published` — Public Feed (Paginated)

**Query Parameters:** `skip=0&limit=10`

**Response `200`:**
```json
{
  "blogs": [...],
  "total": 47,
  "skip": 0,
  "limit": 10,
  "has_more": true
}
```

---

### System Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Database health check |
| `GET` | `/images/{filename}` | Serve blog image from DB (with static fallback) |
| `GET` | `/` | Home page — published blog feed (Jinja2) |
| `GET` | `/posts/{post_id}` | Individual blog post page (Jinja2) |
| `GET` | `/users/{user_id}/posts` | User's published posts page (Jinja2) |
| `GET` | `/login` | Login page |
| `GET` | `/register` | Registration page |
| `GET` | `/dashboard` | Dashboard page |
| `GET` | `/account` | Account settings page |
| `GET` | `/forgot-password` | Forgot password page |
| `GET` | `/reset-password` | Reset password page |

---

## 🔧 Environment Variables

> ⚠️ **Never commit actual values to source control.** Use `.env` for local development and Google Secret Manager for production.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Pooled async PostgreSQL connection string (`postgresql+psycopg://...`) |
| `MIGRATION_DATABASE_URL` | ✅ | — | Direct (non-pooled) PostgreSQL URL for Alembic migrations |
| `TEST_DATABASE_URL` | ❌ | — | Separate database URL for the test suite |
| `SECRET_KEY` | ✅ | — | JWT signing secret (use a 256-bit random hex string) |
| `ALGORITHM` | ❌ | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `30` | JWT token lifespan in minutes |
| `RESET_TOKEN_EXPIRE_MINUTES` | ❌ | `60` | Password reset token lifespan in minutes |
| `OPENAI_API_KEY` | ⚠️ * | — | OpenAI API key (required if LLM_PROVIDER=openai) |
| `GOOGLE_API_KEY` | ⚠️ * | — | Google AI API key (required if LLM_PROVIDER=google) |
| `GROQ_API_KEY` | ⚠️ * | — | Groq API key (required if LLM_PROVIDER=groq) |
| `TAVILY_API_KEY` | ⚠️ * | — | Tavily Search API key (required for research mode) |
| `S3_BUCKET_NAME` | ✅ | — | AWS S3 bucket name for profile images |
| `S3_REGION` | ❌ | —  | AWS region for S3 bucket |
| `S3_ACCESS_KEY_ID` | ✅ | — | AWS access key ID for S3 |
| `S3_SECRET_ACCESS_KEY` | ✅ | — | AWS secret access key for S3 |
| `S3_ENDPOINT_URL` | ❌ | — | Custom S3 endpoint (for LocalStack or MinIO) |
| `MAX_UPLOAD_SIZE_BYTES` | ❌ | `5242880` | Max profile picture size in bytes (default 5 MB) |
| `POSTS_PER_PAGE` | ❌ | `10` | Default pagination size for blog listings |
| `MAIL_SERVER` | ❌ | `localhost` | SMTP server hostname |
| `MAIL_PORT` | ❌ | `587` | SMTP server port |
| `MAIL_USERNAME` | ❌ | `""` | SMTP authentication username |
| `MAIL_PASSWORD` | ❌ | `""` | SMTP authentication password |
| `MAIL_FROM` | ❌ | `noreply@example.com` | From address for outgoing emails |
| `MAIL_USE_TLS` | ❌ | `true` | Enable STARTTLS for SMTP |
| `FRONTEND_URL` | ❌ | `http://localhost:8000` | Base URL for password reset links in emails |

> \* At least one LLM provider key must be configured matching the `LLM_PROVIDER` setting in `config/configuration.yaml`.

### Example `.env` for Local Development

```env
# Database
DATABASE_URL=postgresql+psycopg://user:password@ep-your-neon-pool.neon.tech/blog?sslmode=require
MIGRATION_DATABASE_URL=postgresql+psycopg://user:password@ep-your-neon-direct.neon.tech/blog?sslmode=require
TEST_DATABASE_URL=postgresql+psycopg://user:password@ep-your-neon-direct.neon.tech/blog_test?sslmode=require

# JWT
SECRET_KEY=your-256-bit-random-secret-key-here

# AI Providers
OPENAI_API_KEY=sk-proj-...
TAVILY_API_KEY=tvly-...

# AWS S3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=ap-south-1
S3_ACCESS_KEY_ID=AKIA...
S3_SECRET_ACCESS_KEY=...

# Email (Mailtrap for development)
MAIL_SERVER=sandbox
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_FROM=noreply@yourdomain.com
MAIL_USE_TLS=true

FRONTEND_URL=http://localhost:8000
```

---

## 💻 Local Development Setup

### Prerequisites

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) package manager
- A Neon PostgreSQL account (or local PostgreSQL instance)
- OpenAI API key
- Tavily API key
- AWS S3 bucket (or LocalStack for local testing)

### 1. Clone Repository

```bash
git clone https://github.com/your-username/fastapi_blog_generator.git
cd fastapi_blog_generator
```

### 2. Install UV

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Create Virtual Environment & Install Dependencies

```bash
# Install all dependencies (including dev group)
uv sync --locked --dev

# Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 4. Configure Environment Variables

```bash
# Copy the example template
cp .env.production .env

# Edit with your actual values
# (use your editor of choice)
nano .env
```

### 5. Run Database Migrations

```bash
# Apply all migrations to your database
uv run alembic upgrade head
```

### 6. Configure the LLM Provider

Edit `config/configuration.yaml` to select your preferred LLM provider:

```yaml
llm:
  llm-config:
    LLM_PROVIDER: "openai"       # or "google" or "groq"
    IMAGE_PROVIDER: "openai-image" # or "google-image"
    IMAGE_QUALITY: "medium"      # low | medium | high
```

### 7. Run the FastAPI Application

```bash
# Development server with auto-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Application available at:
- **Web UI:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

### 8. Run Tests

```bash
# Run the full test suite
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_blogs.py -v

# Run with coverage (if coverage is installed)
uv run pytest --cov=src --cov=workflows --cov-report=term-missing
```

---

## 🐳 Docker Setup

### Build the Image

```bash
docker build -t ai-blog-generator:latest .
```

### Run the Container

```bash
docker run -d \
  --name blog-generator \
  -p 8000:8080 \
  --env-file .env \
  ai-blog-generator:latest
```

The container exposes port `8080` internally (controlled by `$PORT` env var). The command above maps it to `8000` on your host.

### Environment Variables in Docker

Pass environment variables via `--env-file` or individual `-e` flags:

```bash
docker run -d \
  -p 8000:8080 \
  -e DATABASE_URL="postgresql+psycopg://..." \
  -e SECRET_KEY="your-secret-key" \
  -e OPENAI_API_KEY="sk-proj-..." \
  ai-blog-generator:latest
```

### Production Build Notes

The `Dockerfile` uses a **multi-stage build**:

1. **Builder stage** (`python:3.14-slim-bookworm` + UV):
   - Copies `pyproject.toml` and `uv.lock`
   - Installs production dependencies only (`--no-dev`)
   - Compiles Python bytecode (`UV_COMPILE_BYTECODE=1`)

2. **Production stage** (`python:3.14-slim-bookworm`):
   - Creates a non-root `appuser` for security
   - Copies the fully-built `/app` from the builder
   - Sets `PYTHONUNBUFFERED=1` for proper log streaming
   - Starts Uvicorn with `--proxy-headers` for Cloud Run compatibility

---

## 🗃 Database Migrations

Alembic is configured to run asynchronously using `MIGRATION_DATABASE_URL` (a direct, non-pooled Neon connection).

### Create a New Migration

After modifying SQLAlchemy models in `schemas/models.py`:

```bash
# Auto-generate migration from model diff
uv run alembic revision --autogenerate -m "describe your change"

# Example:
uv run alembic revision --autogenerate -m "add_tags_to_generated_blogs"
```

> Always review the generated migration file before applying — `--autogenerate` can miss complex changes like type modifications.

### Apply Migrations

```bash
# Upgrade to the latest revision
uv run alembic upgrade head

# Upgrade by a specific number of steps
uv run alembic upgrade +1
```

### Roll Back Migrations

```bash
# Downgrade one revision
uv run alembic downgrade -1

# Downgrade to a specific revision
uv run alembic downgrade 0688fceead1e

# Downgrade to the base (empty schema)
uv run alembic downgrade base
```

### View Migration History

```bash
# Show all revisions
uv run alembic history

# Show current revision
uv run alembic current
```

### Migration Best Practices

- **Never modify** an existing migration file that has been applied to production — create a new revision instead
- Use `MIGRATION_DATABASE_URL` (direct connection) for migrations, never the pooled URL
- Always test migrations against `TEST_DATABASE_URL` before applying to production
- Include both `upgrade()` and `downgrade()` functions in every revision
- In CI/CD, migrations run as a separate **Cloud Run Job** before the new service version is deployed

---

## 🧪 Testing

### Test Architecture

The test suite uses **pytest** with **anyio** for async test support. Tests run against a real Neon `blog_test` database, with AWS S3 mocked using **moto**.

```
tests/
├── conftest.py      # Session-scoped fixtures: engine, database setup, client, mocked S3
├── test_users.py    # User registration, login, profile picture, password reset tests
└── test_blogs.py    # Blog generation (mocked LangGraph), publish, update, delete, like, list tests
```

### Key Test Fixtures

| Fixture | Scope | Description |
|---|---|---|
| `test_engine` | session | Async engine pointing to `TEST_DATABASE_URL` |
| `setup_database` | session | Creates all tables before tests, drops after |
| `db_session` | function | Transactional session with rollback after each test |
| `mocked_aws` | function | `moto` mock with real S3 bucket pre-created |
| `client` | function | `httpx.AsyncClient` with dependency overrides for DB and S3 |

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_blogs.py

# Run specific test by name
uv run pytest -k "test_generate_blog_success"

# Show test output (don't capture)
uv run pytest -s

# Stop on first failure
uv run pytest -x
```

### Test Design Patterns

- **Blog generation tests** mock `generate_blog` with `@patch("src.routers.blogs.generate_blog")` to avoid calling actual LLM APIs in CI
- **Email tests** mock `send_password_reset_email` with `AsyncMock` to verify calls without real SMTP
- **S3 tests** use `moto.mock_aws()` — a context manager that intercepts all `boto3` calls and returns mock responses
- **Transaction isolation** — each test gets a fresh transaction that is rolled back after the test, ensuring a clean state

---

## 🚀 CI/CD Pipeline

### Pipeline Overview

```mermaid
flowchart TD

    PUSH["Git Push"] --> GHA["GitHub Actions"]

    GHA --> TEST["Test Job"]

    TEST --> C["actions/checkout@v4"]
    C --> PY["setup-python@v5<br/>Python 3.13"]

    PY --> UV["setup-uv@v6"]
    UV --> SYNC["uv sync --locked --dev"]
    SYNC --> PYTEST["uv run pytest"]

    PYTEST --> DEPLOY["Deploy Job"]
    PYTEST --> STOP["Pipeline Halted"]

    DEPLOY --> AUTH["OIDC Authentication"]
    AUTH --> GCLOUD["Setup GCloud"]

    GCLOUD --> DOCKER["Configure Docker"]
    DOCKER --> BUILD["Build Docker Image"]

    BUILD --> PUSHIMG["Push To Artifact Registry"]

    PUSHIMG --> CLOUDRUN["Cloud Run Deployment"]

    style PYTEST fill:#2088FF,color:#ffffff
    style CLOUDRUN fill:#4285F4,color:#ffffff
    style AUTH fill:#EA4335,color:#ffffff
```

### Pipeline Details

#### Job 1: `test`

Runs on every push. Sets required environment variables (`DATABASE_URL`, `TEST_DATABASE_URL`, `SECRET_KEY`, S3 mocks) from GitHub repository secrets, then executes the full Pytest suite.

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  TEST_DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
  SECRET_KEY: test-secret-key
  S3_BUCKET_NAME: test-bucket
  AWS_ACCESS_KEY_ID: testing       # moto intercepts these
  AWS_SECRET_ACCESS_KEY: testing
  AWS_DEFAULT_REGION: ap-south-1
```

#### Job 2: `deploy`

Runs only after `test` passes. Uses **Workload Identity Federation (OIDC)** to authenticate to Google Cloud — no long-lived service account keys stored in GitHub.

```yaml
permissions:
  contents: read
  id-token: write    # Required for OIDC token
```

**Deployment command:**
```bash
gcloud run deploy $SERVICE_NAME \
  --image asia-south1-docker.pkg.dev/$PROJECT_ID/$REPO/app:${{ github.sha }} \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=10 \
  --update-secrets=/secrets/app/.env=app-config-prod:latest
```

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `DATABASE_URL` | Neon pooled connection URL |
| `MIGRATION_DATABASE_URL` | Neon direct connection URL |
| `TEST_DATABASE_URL` | Neon test database URL |
| `WORKLOAD_IDENTITY_PROVIDER` | GCP Workload Identity Provider resource name |
| `SERVICE_ACCOUNT` | GCP service account email for deployment |
| `PROJECT_ID` | Google Cloud project ID |
| `REPOSITORY_NAME` | Artifact Registry repository name |
| `SERVICE_NAME` | Cloud Run service name |

---

## ☁️ Google Cloud Deployment

### Required GCP Services

| Service | Purpose |
|---|---|
| **Cloud Run** | Hosts the FastAPI application as a managed container |
| **Artifact Registry** | Stores Docker images (`asia-south1-docker.pkg.dev`) |
| **Secret Manager** | Stores the production `.env` file as `app-config-prod` |
| **IAM / Workload Identity Federation** | Enables keyless GitHub Actions authentication |

### One-Time Setup

#### 1. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create YOUR_REPO_NAME \
  --repository-format=docker \
  --location=asia-south1 \
  --description="AI Blog Generator Docker images"
```

#### 2. Create Secret Manager Secret

```bash
# Upload your production .env file as a secret
gcloud secrets create app-config-prod \
  --data-file=.env.production
```

#### 3. Configure Workload Identity Federation

```bash
# Create a Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create a Provider within the pool
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Bind the provider to your service account
gcloud iam service-accounts add-iam-policy-binding \
  YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_ORG/YOUR_REPO"
```

#### 4. Grant Service Account Permissions

```bash
# Cloud Run deployer
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Artifact Registry writer
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Secret Manager accessor
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Cloud Run Configuration

| Parameter | Value | Notes |
|---|---|---|
| Region | `asia-south1` | Mumbai — adjust to your target region |
| CPU | 2 vCPU | Required for LangGraph + LLM workloads |
| Memory | 2 GiB | Image processing and LLM context buffers |
| Min Instances | 0 | Scales to zero when idle (cost optimization) |
| Max Instances | 10 | Horizontal scaling limit |
| Concurrency | 10 | Requests per instance (LLM calls are I/O bound) |
| Secrets | `app-config-prod:latest` | Mounted at `/secrets/app/.env` |

### Autoscaling Behavior

Cloud Run automatically scales instances based on concurrent requests. With `concurrency=10` and `max-instances=10`, the service can handle up to 100 concurrent requests. Blog generation requests are long-running (30–120 seconds for a full blog), so real concurrency per instance will typically be lower.

---

## 🔒 Security

### JWT Security

- Tokens signed with **HS256** using `SECRET_KEY` (Pydantic `SecretStr` — never logged)
- Required claims enforced: `exp` and `sub`
- `sub` contains the user's integer ID (not username or email)
- Tokens expire in 30 minutes by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Verification fails silently (returns `None`) — the endpoint layer raises `401`

### Password Security

- **Argon2** hashing via `pwdlib[argon2]` — industry-standard memory-hard algorithm
- Passwords are never stored, logged, or returned in any API response
- `verify_password` uses constant-time comparison to prevent timing attacks
- Failed login does not reveal whether the email or password was incorrect

### Password Reset Security

- Reset tokens generated with `secrets.token_urlsafe(32)` (256 bits of entropy)
- Only the **SHA-256 hash** of the token is stored in the database
- Tokens have a 60-minute TTL enforced in application code
- Only one active reset token per user (previous tokens are deleted on new request)
- Reset endpoint returns the same response regardless of email validity (anti-enumeration)

### Secret Management

- All secrets loaded from environment variables via `Pydantic Settings`
- Sensitive fields (`SecretStr`) are masked in logs and `repr()` output
- Production secrets stored in **Google Secret Manager** and mounted as a file at container startup
- No secrets stored in the Docker image or source code

### API Security

- SQL injection prevented by SQLAlchemy parameterized queries (never raw SQL string concatenation)
- All user-owned resources enforce ownership check before modification/deletion (403 if not owner)
- File upload limited to 5 MB (`MAX_UPLOAD_SIZE_BYTES`) with content-type validation via Pillow
- Profile images processed through Pillow before storage (strips EXIF, resizes, re-encodes as JPEG) — prevents polyglot file attacks

### HTTP Security Headers (Middleware)

| Header | Value | Purpose |
|---|---|---|
| `X-Frame-Options` | `SAMEORIGIN` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | Enforce HTTPS (production only) |

### Cloud Security

- Docker container runs as non-root `appuser`
- Workload Identity Federation eliminates long-lived service account key files
- Cloud Run service has no public SSH access
- Database uses SSL/TLS with `sslmode=require` and `channel_binding=require`

---

## 🔧 Troubleshooting

### `OPENAI_API_KEY` Missing

**Symptom:** `BlogGeneratorException: Failed to initialize ModelLoader` on blog generation

**Solution:**
1. Verify the key is set in `.env`: `OPENAI_API_KEY=sk-proj-...`
2. Confirm the `configuration.yaml` matches: `LLM_PROVIDER: "openai"` and `IMAGE_PROVIDER: "openai-image"`
3. Check the key has access to GPT-4o and `gpt-image-2` models in the OpenAI dashboard

---

### Secret Manager Permission Denied

**Symptom:** `403 PERMISSION_DENIED` when Cloud Run starts

**Solution:**
```bash
# Grant Secret Manager accessor role to Cloud Run service account
gcloud secrets add-iam-policy-binding app-config-prod \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

---

### OIDC / Workload Identity Authentication Errors

**Symptom:** GitHub Actions deploy job fails with `google-github-actions/auth` error

**Solutions:**
1. Verify `id-token: write` is in the job `permissions` block
2. Confirm `WORKLOAD_IDENTITY_PROVIDER` secret matches the full resource name: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER`
3. Verify the `attribute.repository` condition matches your exact GitHub org/repo name

---

### Cloud Run Internal Server Error (500) on Startup

**Symptom:** Cloud Run health checks fail immediately after deployment

**Debugging steps:**
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=YOUR_SERVICE" \
  --limit=50 --format="table(timestamp, textPayload)"
```

Common causes:
- Secret at `/secrets/app/.env` is missing or malformed
- `DATABASE_URL` is incorrect or Neon is unreachable from Cloud Run
- Missing required environment variable (check `Settings()` initialization logs)

---

### Neon Database Connection Errors

**Symptom:** `OperationalError: connection refused` or SSL handshake errors

**Solutions:**
1. Verify the connection string includes `?sslmode=require&channel_binding=require`
2. For the application, use the **pooled** endpoint (contains `-pooler` in the hostname)
3. For Alembic migrations, use the **direct** endpoint (no `-pooler`)
4. Check Neon dashboard to confirm the database branch is active

---

### Alembic Migration Failures

**Symptom:** `alembic upgrade head` fails or generates unexpected migrations

**Solutions:**
```bash
# Check current migration state
uv run alembic current

# See what alembic thinks changed
uv run alembic revision --autogenerate --sql  # dry-run, prints SQL only

# Stamp current DB as head (if schema already matches but history is lost)
uv run alembic stamp head
```

**Important:** Always use `MIGRATION_DATABASE_URL` (direct connection) for migrations. Pooled connections will cause session-level DDL to fail.

---

### Artifact Registry Push Failures

**Symptom:** `docker push` fails with `unauthorized: You don't have the required permissions`

**Solution:**
```bash
# Re-authenticate Docker to Artifact Registry
gcloud auth configure-docker asia-south1-docker.pkg.dev

# Verify service account has writer role
gcloud artifacts repositories get-iam-policy YOUR_REPO \
  --location=asia-south1
```

---

### JWT Authentication Errors (401)

**Symptom:** Valid-looking token returns `401 Invalid or expired token`

**Solutions:**
1. Verify `SECRET_KEY` in `.env` matches the key used to sign the token
2. Check token has not expired (default 30 minutes)
3. Ensure the `Authorization` header is formatted exactly as `Bearer <token>` (capital B, space)
4. Confirm the `sub` claim contains a valid integer user ID

---

### Docker Build Failures

**Symptom:** `uv sync` fails during Docker build

**Solutions:**
1. Ensure `uv.lock` is committed and up to date: `uv lock`
2. Verify `pyproject.toml` has all dependencies listed
3. Check Python version compatibility: the Dockerfile uses `python:3.14-slim-bookworm`
4. Clear Docker cache and rebuild: `docker build --no-cache -t ai-blog-generator .`

---

## ⚡ Performance Optimization

### Async SQLAlchemy

All database operations use `async with AsyncSession` and `await` for non-blocking I/O. The `pool_pre_ping=True` setting adds a lightweight `SELECT 1` before each connection use, preventing errors from stale connections without significant overhead.

### Connection Pooling Strategy

The application uses two separate connection strategies:
- **Pooled URL** (`DATABASE_URL`) for the FastAPI application: PgBouncer handles connection multiplexing, allowing many concurrent requests to share a small pool of actual Postgres connections
- **Direct URL** (`MIGRATION_DATABASE_URL`) for Alembic: DDL statements require persistent connections that poolers cannot provide

### Blog Generation — Connection Release

The blog generation endpoint releases the database connection before the long-running LangGraph workflow executes:

```python
await db.rollback()
await db.close()   # Release DB connection to pool during ~60-120 second LLM call
result = await run_in_threadpool(generate_blog, topic)
```

This prevents connection pool exhaustion when multiple users are generating blogs simultaneously.

### LangGraph Thread Pool Execution

LangGraph workflows are synchronous (they block the thread). They are executed in FastAPI's thread pool via `run_in_threadpool()`, preventing the async event loop from being blocked. The event loop remains free to handle health checks and other requests during long generation tasks.

### Parallel Section Writing

The fan-out pattern using LangGraph's `Send` API runs all section writer workers in parallel (not sequentially). A 7-section blog writes all 7 sections simultaneously, not one after another. This reduces total generation time by 60–70% compared to sequential writing.

### Image Pre-loading

Blog images are read from disk into memory before opening the database transaction:

```python
# Step 1: Read from disk (potentially slow)
image_data = file_path.read_bytes()

# Step 2: Open DB session (keep it short)
async with session_maker() as new_db:
    new_db.add(new_blog)
    new_db.add(new_image)   # Already in memory — instant
    await new_db.commit()
```

This minimizes the time the database transaction is held open, reducing contention.

### Cloud Run Concurrency

With `--concurrency=10`, each Cloud Run instance handles 10 simultaneous requests. Since LangGraph runs in a thread pool and database operations are async, the event loop can interleave lightweight requests (health checks, reads) while long blog generation tasks run in worker threads.

### Image Storage in Database

Blog images are stored as `LargeBinary` in PostgreSQL rather than on the container filesystem. This eliminates the need for a persistent volume or external object storage for blog images, and the images survive container restarts and scaling events.

---

## 🔮 Future Improvements

| Feature | Description |
|---|---|
| **Blog SEO Optimization** | Auto-generate meta descriptions, keywords, and structured data (JSON-LD) |
| **Multi-Language Blogs** | Support blog generation in Spanish, French, German, Japanese, etc. |
| **Vector Database Integration** | Embed generated blogs in a vector DB (Pinecone/Weaviate) for semantic search |
| **RAG Pipelines** | Retrieve previous blogs as context to avoid content duplication |
| **Blog Scheduling** | Schedule blog generation and auto-publish at a specified time |
| **Analytics Dashboard** | Track blog views, unique visitors, like trends, and topic performance |
| **Team Collaboration** | Multi-user workspaces with roles (admin, editor, viewer) |
| **Webhook Integration** | Post-publish webhooks to notify CMS, Slack, or Discord |
| **OpenAI Fine-Tuning** | Fine-tune on high-performing blogs to improve output quality over time |
| **Draft Versioning** | Keep revision history for each blog with diff comparison |
| **Comment System** | Reader comments with moderation queue |
| **RSS Feed** | Auto-generated RSS/Atom feed for published blogs |
| **Blog Categories / Tags** | Organize blogs by topic area with filterable feeds |
| **Email Newsletter** | Automatically email subscribers on new blog publication |
| **Rate Limiting** | Per-user generation rate limits to control API costs |
| **Streaming Generation** | Stream blog sections to the client as they are written (SSE) |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

### Development Workflow

1. **Fork** the repository and create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Install dependencies** (including dev tools):
   ```bash
   uv sync --locked --dev
   ```

3. **Make your changes** — keep commits atomic and descriptive

4. **Add tests** for any new functionality:
   - User-facing features → `tests/test_users.py` or `tests/test_blogs.py`
   - New database models → add migration with `alembic revision --autogenerate`

5. **Run the test suite** and ensure it passes:
   ```bash
   uv run pytest -v
   ```

6. **Push your branch** and open a Pull Request against `main`

### Code Style Guidelines

- Follow PEP 8 (enforced by `isort` for imports)
- Use type hints on all function signatures
- Add docstrings to all public functions and classes
- Keep router functions thin — move business logic to service modules
- Use `Annotated[AsyncSession, Depends(get_db)]` pattern for dependency injection
- Raise `HTTPException` (not custom exceptions) from router functions
- Raise `BlogGeneratorException` from workflow and service functions

### Commit Message Convention

```
feat: add blog scheduling endpoint
fix: resolve connection pool exhaustion under concurrent generation
refactor: extract image upload logic to dedicated service module
docs: update API documentation for /api/blogs/generate
test: add integration tests for password reset flow
chore: upgrade langgraph to 1.2.0
```

### Reporting Bugs

Please open a GitHub Issue with:
- A clear title and description
- Steps to reproduce
- Expected vs. actual behavior
- Relevant log output or error messages
- Environment details (Python version, OS, deployment target)

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Sourav Raj

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

Built with ❤️ using FastAPI · LangGraph · OpenAI · Neon PostgreSQL · Google Cloud Run

</div>
