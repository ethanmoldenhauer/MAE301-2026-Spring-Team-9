from pathlib import Path

APP_TITLE = "NestGPT Source-Backed MVP"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4.1-mini"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LOGO_CANDIDATES = ["logo.png", "logo.jpg", "logo.jpeg", "logo.webp"]
DATA_DIR = Path("data/processed")
DB_PATH = Path("storage/nestgpt.db")
MAX_RETRIEVAL_RESULTS = 6
DISCLAIMER = (
    "NestGPT is a planning assistant for housing abroad. It is not legal advice, "
    "immigration advice, or a substitute for official government guidance."
)
SUPPORTED_COUNTRIES = ["Germany", "Portugal", "Japan"]
TOPICS = ["housing", "visa", "costs", "general"]
