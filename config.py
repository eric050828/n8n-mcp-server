"""
Configuration for the n8n MCP Server.
"""
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv
from n8n_sdk_python.client import N8nClient

# Load environment variables from .env file
load_dotenv()

# Logging Configuration
logging.getLogger(__name__)
handlers: List[logging.Handler] = []
try:
    from rich.console import Console
    from rich.logging import RichHandler
    handlers.append(RichHandler(console=Console(stderr=True), rich_tracebacks=True))
except ImportError:
    pass

if not handlers:
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(message)s",
    handlers=handlers,
    encoding="utf-8" # Ensure UTF-8 for logging output
)

# n8n API Connection Configuration
N8N_BASE_URL: str = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY: Optional[str] = os.getenv("N8N_API_KEY")

# Create n8n client instance (to be shared)
n8n_client: Optional[N8nClient] = None
try:
    n8n_client = N8nClient(base_url=N8N_BASE_URL, api_key=N8N_API_KEY)
    logging.info(f"Successfully initialized n8n_client for {N8N_BASE_URL}")
except Exception as e:
    logging.error(f"Failed to initialize n8n_client: {e}", exc_info=True)
    # Fallback or exit if n8n_client is critical
    n8n_client = None # Or raise an exception

# Node Data Paths Configuration
NODE_DATA_BASE_PATH: str = os.getenv("NODE_DATA_BASE_PATH", os.path.join(os.getcwd(), "node_data"))
CATEGORY_CLASSIFICATION_FILE_PATH: str = os.getenv(
    "CATEGORY_CLASSIFICATION_PATH", 
    os.path.join(NODE_DATA_BASE_PATH, "category_classification_result.json")
)
CLASS_CLASSIFICATION_FILE_PATH: str = os.getenv(
    "CLASS_CLASSIFICATION_PATH",
    os.path.join(NODE_DATA_BASE_PATH, "class_classification_result.json")
)
NODE_CATEGORIES_PATH_BASE: str = os.path.join(NODE_DATA_BASE_PATH, "categories")
NODE_CLASSES_PATH_BASE: str = os.path.join(NODE_DATA_BASE_PATH, "classes")

# Log configured paths for verification
logging.debug(f"NODE_DATA_BASE_PATH: {NODE_DATA_BASE_PATH}")
logging.debug(f"CATEGORY_CLASSIFICATION_FILE_PATH: {CATEGORY_CLASSIFICATION_FILE_PATH}")
logging.debug(f"CLASS_CLASSIFICATION_FILE_PATH: {CLASS_CLASSIFICATION_FILE_PATH}")

# Ensure critical configurations are present
if not N8N_BASE_URL:
    logging.error("N8N_BASE_URL is not set in environment variables or .env file.")
if n8n_client is None:
    logging.error("n8n_client could not be initialized. Check N8N_BASE_URL and N8N_API_KEY.") 