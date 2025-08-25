# Tasky AI

An AI-powered task management system that operates through WhatsApp, built using Google's ADK (Agent Development Kit) for Python.

## Overview

Tasky AI is an intelligent task management agent that helps users organize and manage their tasks efficiently through natural language conversations on WhatsApp. The system uses language models to understand user intent and manage tasks accordingly with database integration.

## Features

- Natural language task management through WhatsApp
- Intelligent task creation and organization
- Priority-based task scheduling
- Flexible datetime parsing for due dates
- Tag-based task categorization
- Task status tracking (pending, in progress, completed, archived)
- Smart task retrieval and filtering
- Multi-user support with individual task management

## Technical Stack

- **Backend Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Agentic Framework**: Google ADK with Gemini 2.0
- **Messaging**: WhatsApp Cloud API
- **Authentication**: WhatsApp-based user verification
- **Deployment**: Docker containerization, Google Cloud Run

## Project Structure

```
tasky-ai/
├── api_server/         # FastAPI server implementation
├── tasky_agent/       # AI agent and tools implementation
├── supabase/         # Database migrations and configuration
└── main.py          # Application entry point
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Configure the following environment variables:
   - WhatsApp Cloud API credentials
   - Supabase configuration
   - Google Cloud configuration

## Deployment

The project includes a Dockerfile for containerized deployment. Build and run using:

```bash
docker build -t tasky-ai .
docker run -p 8080:8080 tasky-ai
```

## Upcoming Features

- Voice message input support
- Smart reminders and notifications

## Development Status

This project is actively maintained and under development. Contributions are welcome.

> **Note**: Real-world testing of the WhatsApp integration is coming soon, pending Meta Business verification. This verification is required to move the WhatsApp integration from development to production status.

## License

Tasky AI © 2025 by [Vamsi Anem](https://github.com/anemvamsi4) is licensed under 
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

See [LICENSE](./LICENSE) for full terms.