"""
Main entry point for the n8n MCP Server.
Imports the application instance and component modules to trigger decorator-based registration.
"""
import os
import logging

# Import the FastMCP application instance from mcp_server.py
from mcp_server import app

# Import component modules to ensure their decorators are executed and components are registered with the app instance.
import mcp_components.tools
import mcp_components.resources
import mcp_components.prompts

# Configurations from config.py
from config import n8n_client, CATEGORY_CLASSIFICATION_FILE_PATH, CLASS_CLASSIFICATION_FILE_PATH

# Main execution block
if __name__ == "__main__":
    logging.info(f"Starting n8n MCP Server ({app.name})...")
    
    if not n8n_client:
        print("Error: n8n_client is not initialized. Server may not function correctly.")
        logging.error("n8n_client is not initialized at startup.")

    if not os.path.exists(CATEGORY_CLASSIFICATION_FILE_PATH):
        print(f"Warning: Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}")
        logging.warning(f"Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}")

    if not os.path.exists(CLASS_CLASSIFICATION_FILE_PATH):
        print(f"Warning: Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}")
        logging.warning(f"Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}")

    try:
        # Run the server using stdio transport by default
        app.run(transport=os.getenv("MCP_SERVER_TRANSPORT", "stdio"))
    except KeyboardInterrupt:
        print("\nServer interrupted by user. Shutting down.")
        logging.info("Server interrupted by user. Shutting down.")
    except Exception as e:
        print(f"Server failed to start or run: {str(e)}")
        logging.error(f"Server critical failure: {str(e)}", exc_info=True) 