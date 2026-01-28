import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_KEY_HERE")

# OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

# RAG API
RAG_API_URL = os.getenv("RAG_API_URL", "YOUR_API_URL_HERE")

# Agent settings
MAX_ITERATIONS = 5
CLAUDE_MAX_TOKENS = 4096
