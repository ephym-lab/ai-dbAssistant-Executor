# AI SQL Assistant

An intelligent SQL query generator that converts natural language to safe, correct SQL queries using AI.

## Features

- 🤖 **Multi-Provider Support**: Switch between OpenAI (GPT-4) and Google Gemini
- 🔌 **REST API**: FastAPI-based endpoint for integration
- 💻 **CLI Interface**: Interactive command-line tool
- 🛡️ **Safety First**: Never executes queries, only generates them
- 📝 **Schema-Aware**: Optional database schema context for accurate queries

## Setup

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment** (create `.env` file):
   ```env
   # Choose your provider
   AI_PROVIDER=openai  # or 'gemini'
   
   # Add your API key
   OPENAI_API_KEY=sk-your-key-here
   # OR
   GEMINI_API_KEY=your-gemini-key-here
   ```

## Usage

### REST API

1. **Start the Server**:
   ```bash
   cd src
   uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Test the API**:
   ```bash
   # Basic query
   curl -X POST http://localhost:8000/generate-sql \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me all users"}'
   
   # With schema context
   curl -X POST http://localhost:8000/generate-sql \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Get all active users",
       "db_schema": "CREATE TABLE users (id INT, name VARCHAR, active BOOLEAN);"
     }'
   ```

3. **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs

### CLI Interface

```bash
python src/main.py
```

Then type your questions interactively.

## API Endpoints

### `POST /generate-sql`

Generate SQL from natural language.

**Request Body**:
```json
{
  "question": "your natural language question",
  "db_schema": "optional database schema"
}
```

**Response**:
```json
{
  "content": "explanation of the query",
  "query": "SELECT * FROM users;"
}
```

### `GET /health`

Health check endpoint.

### `GET /`

API information and available endpoints.

## Project Structure

```
DBAssistantMl/
├── src/
│   ├── api.py           # FastAPI server
│   ├── main.py          # CLI interface
│   ├── ai_service.py    # AI provider abstraction
│   └── prompts.py       # System prompts
├── requirements.txt
└── .env                 # Configuration (create this)
```

## Switching Providers

Simply change the `AI_PROVIDER` in your `.env` file:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

No code changes needed!

## Development

Run with auto-reload:
```bash
cd src
uvicorn api:app --reload
```

## Safety Features

- ✅ Never executes SQL queries
- ✅ Validates JSON responses
- ✅ Warns on dangerous operations
- ✅ Requires explicit schema or uses safe defaults
- ✅ PostgreSQL-compliant syntax by default
