"""
Centralized FastMCP application instance creation.
"""
import os
import logging
from typing import Any
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

# Import configurations needed for lifespan and app setup
from config import (
    N8N_BASE_URL, N8N_API_KEY,
    CATEGORY_CLASSIFICATION_FILE_PATH, CLASS_CLASSIFICATION_FILE_PATH,
    n8n_client
)

# Lifespan handler now resides here to be bundled with app creation
@asynccontextmanager
async def lifespan_handler(app_instance: FastMCP) -> Any:
    """Lifespan handler for the MCP server application."""
    logging.info(f"MCP Server ({app_instance.name}) starting up via lifespan...")
    if not n8n_client:
        logging.error("Lifespan: n8n_client is not initialized. MCP server might not function correctly.")
    else:
        logging.info(f"Lifespan: n8n_client confirmed initialized for {N8N_BASE_URL}")

    if not os.path.exists(CATEGORY_CLASSIFICATION_FILE_PATH):
        logging.error(f"Lifespan: Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}")
    else:
        logging.info(f"Lifespan: Category classification file found: {CATEGORY_CLASSIFICATION_FILE_PATH}")
    
    if not os.path.exists(CLASS_CLASSIFICATION_FILE_PATH):
        logging.error(f"Lifespan: Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}")
    else:
        logging.info(f"Lifespan: Class classification file found: {CLASS_CLASSIFICATION_FILE_PATH}")
    
    yield
    
    logging.info(f"MCP Server ({app_instance.name}) shutting down via lifespan...")

# Create the global FastMCP application instance
app = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "n8n-mcp-server"),
    instructions="This is an n8n MCP server providing tools for workflow, node, and tag management.",
    json_response=True,
    lifespan=lifespan_handler,
    log_level=os.getenv("LOG_LEVEL", "INFO").upper()
)

logging.info(f"FastMCP app instance created: {app.name}") 