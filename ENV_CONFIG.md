# Environment Configuration

This project requires environment variables to be set in a `.env` file in the root directory.

## Required Configuration

### OpenRouter API (Recommended)

The project is configured to use OpenRouter for LLM inference. Create a `.env` file with:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**Get your API key from:** https://openrouter.ai/

## Optional: Alternative LLM Providers

### Vertex AI (Google Cloud)

If you prefer to use Vertex AI instead of OpenRouter, add these variables:

```bash
VERTEX_AI_PROJECT_ID=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1
```

## Setup Instructions

1. Create a `.env` file in the project root:
   ```bash
   touch .env
   ```

2. Add your API key:
   ```bash
   echo "OPENROUTER_API_KEY=your_actual_api_key" >> .env
   ```

3. The `.env` file is already in `.gitignore` and will not be committed to version control.

## Example .env File

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Verifying Configuration

Run this command to check if your environment is set up correctly:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ OPENROUTER_API_KEY found' if os.getenv('OPENROUTER_API_KEY') else '✗ OPENROUTER_API_KEY not found')"
```


