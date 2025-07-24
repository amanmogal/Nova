# Autonomous Notion Agent

An AI agent that autonomously manages and schedules tasks within a Notion database using RAG (Retrieval Augmented Generation) for intelligent decision-making.

## Project Overview

This agent acts as a "Digital Personal Assistant" for Notion by:
- Monitoring your Notion task database and contextual cues
- Retrieving relevant task details and preferences using RAG
- Using LLM (Gemini 1.5 Flash) to intelligently plan and schedule tasks
- Executing actions to update Notion properties or send notifications
- Operating autonomously on a scheduled basis

## 12-Factor Agent Architecture

This project follows the 12-Factor Agent framework to ensure reliability, maintainability, and production readiness:

1. Natural Language to Tool Calls
2. Own Your Prompts
3. Own Your Context Window
4. Tools are Just Structured Outputs
5. Unify Execution State and Business State
6. Launch/Pause/Resume with Simple APIs
7. Contact Humans with Tool Calls
8. Own Your Control Flow
9. Compact Errors into Context Window
10. Small, Focused Agents
11. Trigger from Anywhere
12. Make Your Agent a Stateless Reducer

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` (see `.env.example`)
4. Configure your Notion database schema
5. Run the initialization script: `python src/setup.py`

## Usage

Once set up, the agent will run automatically according to the configured schedule.

For manual invocation:
```
python src/agent.py
``` 
