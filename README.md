# Tasky AI

An AI-powered task management system that operates through WhatsApp, built using Google's ADK (Agent Development Kit) for Python.

**🔗 Landing Page: [https://tasky-ai.krishna-vamsi.me](https://tasky-ai.krishna-vamsi.me)**
**💬 Start Chatting: [wa.me/917680835913](https://wa.me/917680835913)**

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

## How to Use the WhatsApp Bot

1. Visit the [Tasky AI Landing Page](https://tasky-ai.krishna-vamsi.me) for information on how to get started
2. Click the WhatsApp button on the landing page or use this direct link: [wa.me/917680835913](https://wa.me/917680835913)
3. Start a conversation with Tasky AI on WhatsApp
4. Use natural language to create, update, view, and manage your tasks

Example commands:
- "Create a task to finish the presentation by tomorrow afternoon"
- "Show me all my pending tasks"
- "Mark the meeting with John as completed"
- "What are my high priority tasks due this week?"

## Development Status

This project is actively maintained and under development. Contributions are welcome.

The WhatsApp bot is now fully functional and operational. Users can interact with Tasky AI through WhatsApp to manage their tasks using natural language commands.

## License

Tasky AI © 2025 by [Vamsi Anem](https://github.com/anemvamsi4) is licensed under 
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

See [LICENSE](./LICENSE) for full terms.