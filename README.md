# Aierpify Backend - FastAPI Backend for Garment Try-On System

Welcome to the **Aierpify Backend**, the FastAPI-based backend for **Aierpify**, a modern ERP system. This repository serves as the core backend that handles authentication, database operations and much more.

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Setup Guide](#setup-guide)
  - [1. Cloning the Repository](#1-cloning-the-repository)
  - [2. Creating a Virtual Environment And Installing Dependencies](#2-creating-a-virtual-environment-and-installing-dependencies)
  - [3. Setting up Environment Variables](#3-setting-up-environment-variables)
  - [4. Running the Application](#4-running-the-application)
- [Project Structure](#project-structure)
- [Creating a New Module](#creating-a-new-module)
- [Routing and Merge Conflict Prevention](#routing-and-merge-conflict-prevention)
- [Coding Standards and Best Practices](#coding-standards-and-best-practices)
  - [1. Full Type Annotations](#1-full-type-annotations)
  - [2. All Functions, Routes, and Classes Must Include Docstrings](#2-all-functions-routes-and-classes-must-include-docstrings)
  - [3. Using Pydantic v2 for Input and Output Models](#3-using-pydantic-v2-for-input-and-output-models)
  - [4. Async Functions and Routes](#4-async-functions-and-routes)
  - [5. Handling Long Running Tasks](#5-handling-long-running-tasks)
  - [6. Proper FastAPI Docs Setup](#6-proper-fastapi-docs-setup)
- [Release Management](#release-management)
- [Branching Strategy](#branching-strategy)
- [Maintainer](#maintainer)
- [Contributing Guidelines](#contributing-guidelines)
- [FastAPI Development Guidelines](#fastapi-development-guidelines)
  - [Basic Guidelines](#1-basic-guidelines)
  - [Advanced Development Practices](#2-advanced-development-practices)

---

## Project Overview

This backend service is built using FastAPI to provide a scalable and high-performance API for Aierpify, a modern ERP system. The backend handles authentication, user management, and API interactions.

---

## Tech Stack

The backend utilizes the following technologies:

- **FastAPI** - The core web framework
- **Postgresql** - The database
- **Better Auth** - For user authentication and authorization
- **Pydantic v2** - For data validation and serialization
- **SQLAlchemy/SQLModel** - ORM for database interactions (No raw SQL queries)
- **Alembic** - Database migrations
- **Uvicorn/Socketify** - ASGI server for running FastAPI

## Setup Guide

[!CAUTION]
Please install uv by astral for python package and venv management.
[Astral UV](https://docs.astral.sh/uv/)

### 1. Cloning the Repository

```sh
git clone https://github.com/aierpify/aierpify-backend.git
cd aierpify-backend
```

### 2. Creating a Virtual Environment And Installing Dependencies

Next we create a virtual environment and install the required dependencies.
The `uv` tool will automatically create and manage the virtual environment for you.

[!TIP]
Use Python 3.13.0 or higher.

```sh
uv sync
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate  # On Windows
```

### 3. Setting up Environment Variables

- Copy `.env.example` and rename it to `.env`
- Copy `example.settings.toml` and rename it to `settings.toml`
- Copy `example.secrets.toml` and rename it to `.secrets.toml`
- Update the environment variables in `.env` and the settings/secrets in `settings.toml` and `secrets.toml` respectively.

### 4. Running the Application

Start the FastAPI backend with:

```sh
uvicorn src.main:app --reload
```

OR

```sh
fastapi dev src/main.py
```

Docker Setup In Progress. (Available Soon)

---

## Project Structure

```text
└── 📁aierpify-backend
    ├── 📁requirements
    │   ├── base.txt
    │   ├── dev.txt
    │   ├── prod.txt
    ├── 📁src
    │   ├── __init__.py
    │   ├── config.py
    │   ├── database.py
    │   ├── exceptions.py
    │   ├── main.py
    │   ├── models.py
    │   ├── 📁module_template
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   ├── constants.py
    │   │   ├── dependencies.py
    │   │   ├── exceptions.py
    │   │   ├── models.py
    │   │   ├── router.py
    │   │   ├── schemas.py
    │   │   ├── service.py
    │   │   ├── tasks.py
    │   │   ├── utils.py
    ├── 📁templates
    │   ├── index.html
    ├── .env
    ├── .gitignore
    ├── example.secrets.toml
    ├── example.settings.toml
    ├── README.md
    ├── secrets.toml
    ├── settings.toml
```

---

## Creating a New Module

To create a new module:

1. Copy the `src/module_template` folder.
2. Rename it to the new module name.
3. Implement your module-specific logic in:
   - `router.py` - is a core of each module with all the endpoints
   - `schemas.py` - for pydantic models
   - `models.py` - for db models
   - `service.py` - module specific business logic
   - `dependencies.py` - router dependencies
   - `constants.py` - module specific constants and error codes
   - `config.py` - e.g. module specific env vars and settings
   - `utils.py` - non-business logic functions, e.g. response normalization, data enrichment, etc.
   - `exceptions.py` - module specific exceptions, e.g. PostNotFound, InvalidUserData
   - `tasks.py` - long running tasks, e.g. image processing, email sending, etc.

---

## Routing and Merge Conflict Prevention

- Each module should define its own `router.py` file.
- Import and include all routers in `src/main.py`:

  ```python
  from fastapi import FastAPI
  from src.module_name.router import router as module_router

  app = FastAPI()

  app.include_router(module_router, prefix="/module-name", tags=["Module Name"])
  ```

- This ensures minimal merge conflicts when multiple developers work on different modules.

---

## Coding Standards and Best Practices

### 1. Full Type Annotations

All functions must include full type annotations.

```python
async def get_user(user_id: str) -> dict:
```

### 2. All Functions, Routes, and Classes Must Include Docstrings

All functions, routes, and classes must include docstrings explaining their purpose, arguments, and return values.
Use Google-style docstrings for consistency.
Read more about [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

- **Functions**: Include a docstring explaining the function's purpose.
- **Routes**: Include a docstring explaining the route's purpose and expected input/output.
- **Classes**: Include a docstring explaining the class's purpose and attributes/methods.

```python
async def get_user(user_id: str) -> dict:
    """
    Get user details by user ID.

    Args:
        user_id (str): The user ID.

    Returns:
        dict: User details.
    
    Raises:
        UserNotFoundError: If the user is not found.
    """

    # Function logic here
```

### 3. Using Pydantic v2 for Input and Output Models

- Input and output validation should always use Pydantic models.

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
```

### 4. Async Functions and Routes

- Always use `async` functions for FastAPI routes.

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
async def get_items():
    return {"items": []}
```

### 5. Handling Long Running Tasks

- **Short-running** tasks go in `utils.py`, `service.py`, or `router.py`.
- **Long-running** tasks must be moved to `tasks.py` and handled using Celery.

```python
from celery import Celery

celery = Celery("tasks", broker="redis://localhost:6379/0")

@celery.task
def process_image(image_url: str):
    # Long-running image processing logic
    return {"status": "completed"}
```

### 6. Proper FastAPI Docs Setup

- **FastAPI Docs**: FastAPI automatically generates API documentation based on the route docstrings, Pydantic models, and responses.
- **Swagger UI**: The Swagger UI is available at `http://localhost:8000/docs` for testing and exploring the API.
- **Redoc**: The Redoc UI is available at `http://localhost:8000/redoc` for an alternative API documentation view.
- **Custom Exceptions**: Use custom exceptions to handle errors and return appropriate responses.
- **Custom Responses**: Use Pydantic models to define custom responses for each route.

```python
from fastapi import APIRouter, status

router = APIRouter()

@router.post(
    "/endpoints",
    response_model=DefaultResponseModel,  # default response pydantic model
    status_code=status.HTTP_201_CREATED,  # default status code
    description="Description of the well documented endpoint",
    tags=["Endpoint Category"],
    summary="Summary of the Endpoint",
    responses={
        status.HTTP_200_OK: {
            "model": OkResponse, # custom pydantic model for 200 response
            "description": "Ok Response",
        },
        status.HTTP_201_CREATED: {
            "model": CreatedResponse,  # custom pydantic model for 201 response
            "description": "Creates something from user request ",
        },
        status.HTTP_202_ACCEPTED: {
            "model": AcceptedResponse,  # custom pydantic model for 202 response
            "description": "Accepts request and handles it later",
        },
    },
)
async def documented_route():
    pass
```

---

## Release Management

- **Semantic Versioning (SemVer)**
  - Format: `MAJOR.MINOR.PATCH` (e.g., `1.0.0`)
- **Production Releases**
  - All releases will be tagged manually on the `main` branch.

---

## Branching Strategy

- **Feature branches** → Merge into `main` via pull request.
- Only **DanyaalMajid** has merge/review permissions for PRs.
- Releases will always be tagged on `main`.

---

## Maintainer

**DanyaalMajid** is the repository maintainer, responsible for:

- Reviewing and merging pull requests
- Managing releases
- Ensuring project consistency

---

## Contributing Guidelines

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`
3. Commit and push changes.
4. Open a pull request to `main`.
5. Await review and merge by the maintainer.

---

## FastAPI Development Guidelines

To ensure high-quality, scalable, and maintainable FastAPI development, we adhere to **best practices** inspired by industry standards and community-driven recommendations.

### 1. Basic Guidelines

For a solid foundation in FastAPI development, refer to the [FastAPI Best Practices Repository](https://github.com/zhanymkanov/fastapi-best-practices). This guide covers:

- **Project structuring** for scalability
- **Asynchronous programming** principles
- **Dependency injection best practices**
- **Pydantic usage** for data validation and serialization
- **Database migrations with Alembic**
- **RESTful API design principles**
- **Security best practices** (JWT, OAuth2, etc.)

### 2. Advanced Development Practices

For **enhanced** FastAPI development, refer to [Issue #4 in the same repository](https://github.com/zhanymkanov/fastapi-best-practices/issues/4), which outlines:

- **Optimized permission and authentication handling**
- **Class-based services and views** for better modularity
- **Task queue management** with Celery for background processing
- **Custom response serializers** to improve API performance
- **Efficient configuration management** using Dynaconf
- **Integration testing best practices** with async test clients

By following these **best practices**, we maintain code consistency, improve performance, and ensure a seamless developer experience in the **Aierpify Backend**. 🚀
