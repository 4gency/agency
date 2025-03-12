# LinkedIn Bot Mock

This is a mock bot for simulating job applications on LinkedIn, designed to integrate with the backend system through webhook APIs.

## Features

- Simulation of the LinkedIn login process (with 2FA possibility)
- Job search based on user configurations
- Job applications with random intervals between 10 and 60 seconds
- Support for user action requests (2FA, CAPTCHA, questions)
- Registration of successful and failed applications (10% chance of failure)
- Detailed events for progress tracking
- YAML configuration validation
- Support for application limits

## Environment Variables

```
API_PORT=8080                 # Port for the bot API
LINKEDIN_EMAIL=email@example.com # LinkedIn email
LINKEDIN_PASSWORD=password123  # LinkedIn password
APPLY_LIMIT=200               # Application limit
STYLE_CHOICE=Modern Blue      # Resume style
SEC_CH_UA=...                 # User-Agent Client Hints header
SEC_CH_UA_PLATFORM=Windows    # User-Agent platform
USER_AGENT=...                # Complete User-Agent
BACKEND_TOKEN=secret_key      # Token for backend authentication
BACKEND_URL=http://api:5000   # Backend URL
BOT_ID=1234                   # Bot ID
GOTENBERG_URL=http://gotenberg:3000 # Gotenberg service URL (optional)
```

## Available Styles

- "Cloyola Grey"
- "Modern Blue" 
- "Modern Grey"
- "Default"
- "Clean Blue"

## Running with Docker

To run the bot using Docker:

```bash
docker build -t linkedin-bot-mock .
docker run -p 8080:8080 --env-file .env linkedin-bot-mock
```

## Running with Docker Compose

To run the bot using Docker Compose:

```bash
docker-compose up -d
```

## Bot API

The bot exposes an API to interact with it:

- `GET /health` - Checks if the bot is working
- `POST /action/<action_id>` - Endpoint to receive responses for user actions

## Execution Flow

1. Bot starts and validates environment variables
2. Bot retrieves configurations and resume from the backend
3. Bot simulates LinkedIn login (may request 2FA)
4. Bot navigates to the job search page
5. Bot starts the search and application loop:
   - Finds a job
   - Checks if company/title is blacklisted
   - Simulates the application process (may request CAPTCHA)
   - Registers application (success or failure)
   - Waits between 10 and 60 seconds before the next application
6. Bot finishes when it reaches the application limit

## Generated Events

The bot generates various events for monitoring:

- `starting` - Starting the bot
- `running` - Bot running
- `paused` - Bot paused
- `waiting` - Waiting for user action
- `completed` - Bot successfully completed
- `failed` - Bot finished with error
- `stopping` - Bot finishing

In addition to these, other specific events are generated during the application process, such as:

- `navigating` - Navigating to a page
- `login` - Filling credentials
- `logged_in` - Login successful
- `search_started` - Starting job search
- `job_found` - Job found
- `job_skipped` - Job skipped
- `apply_started` - Starting application
- `apply_success` - Application successful
- `apply_failed` - Application failure
- `progress_update` - Progress update

## User Actions

The bot may request user actions at certain times:

- `PROVIDE_2FA` - Provide two-factor verification code
- `SOLVE_CAPTCHA` - Solve a CAPTCHA
- `ANSWER_QUESTION` - Answer a custom question

## Logs

The bot generates detailed logs in:

- Console (colored)
- File `logs/bot_mock.log` 