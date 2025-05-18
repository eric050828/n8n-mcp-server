'''
Defines MCP resources for accessing n8n data like workflows, node types, and tags.
'''
import logging
import json
import os
from typing import Any, Optional

# Import shared configurations and n8n client
from config import n8n_client, CATEGORY_CLASSIFICATION_FILE_PATH, CLASS_CLASSIFICATION_FILE_PATH, NODE_DATA_BASE_PATH
from mcp_server import app
from n8n_sdk_python.models.workflows import Workflow

# Note: Resource functions will be registered in main.py using app.resource_manager.add_resource
# or by wrapping them with a Resource class if the SDK requires specific objects.
# For now, we define the provider functions.

@app.resource("n8n:/workflow/{workflow_id}", description="Provides workflow data for a specific n8n workflow.")
async def get_workflow_resource_data(workflow_id: str) -> dict[str, Any]:
    """
    Retrieves complete workflow definition data as a resource.
    
    This resource provides direct access to workflow definition data, including
    nodes, connections, settings, and metadata. The response structure follows
    the n8n_sdk_python.models.workflows.Workflow model specification.
    
    Args:
        workflow_id: The unique identifier of the workflow to retrieve.

    Returns:
        Complete workflow definition object, or error information on failure.
        Success response contains all workflow properties including:
        - id: Workflow identifier
        - name: Workflow name
        - nodes: Array of processing nodes
        - connections: Data flow configuration
        - settings: Execution settings
        - active: Activation status
        - tags: Associated tags (if any)
        
        Error response contains:
        - error: Error description
        - status_code: HTTP status code
    """
    if not n8n_client:
        logging.error("get_workflow_resource_data: n8n_client is not initialized.")
        # MCP resource functions should ideally return a structure indicating an error,
        # or the MCP framework might have a way to handle exceptions raised here.
        # For simplicity, returning an error dict. The framework might expect an exception.
        return {"error": "n8n_client not initialized", "status_code": 500} 
    try:
        workflow: Workflow = await n8n_client.get_workflow(workflow_id=workflow_id) 
        return workflow.model_dump(exclude_none=True)
    except Exception as e:
        logging.error(f"Error fetching workflow resource {workflow_id}: {e}", exc_info=True)
        return {"error": f"Error fetching workflow {workflow_id}: {str(e)}", "status_code": 500}

@app.resource("n8n:/node-types", description="Provides information on available n8n node types from local classification files.")
async def get_node_types_resource_data() -> dict[str, Any]:
    """
    Retrieves a comprehensive registry of available node types with metadata.
    
    This resource provides a consolidated view of all node types from both category
    and class classification files. Each node entry includes display name and 
    categorical grouping information to assist in workflow construction.
    
    Returns:
        A dictionary containing node type registry information, or error data on failure.
        Success response structure:
        {
            "node_types": {
                "node-type-identifier": {
                    "displayName": "User-friendly Name",
                    "group": "Category or Class grouping"
                },
                // Additional node types...
            }
        }
        
        Error response structure:
        {
            "error": "Error description",
            "status_code": 500
        }
    """
    all_nodes: dict[str, dict[str, str]] = {}
    try:
        category_data: dict[str, Any] = {}
        class_data: dict[str, Any] = {}
        if os.path.exists(CATEGORY_CLASSIFICATION_FILE_PATH):
            with open(CATEGORY_CLASSIFICATION_FILE_PATH, 'r', encoding='utf-8') as f:
                category_data = json.load(f)
        else:
            logging.warning(f"Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}")
            return {"error": f"Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}", "status_code": 500}
            
        if os.path.exists(CLASS_CLASSIFICATION_FILE_PATH):
            with open(CLASS_CLASSIFICATION_FILE_PATH, 'r', encoding='utf-8') as f:
                class_data = json.load(f)
        else:
            logging.warning(f"Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}")
            return {"error": f"Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}", "status_code": 500}
        
        for cat_name, nodes in category_data.get('categories', {}).items():
            for node in nodes:
                node_type_name = node.get('type')
                if not node_type_name: continue
                all_nodes[node_type_name] = {
                    "displayName": node.get('name', node_type_name),
                    "group": f"Category: {cat_name}"
                }
        
        for class_name, nodes in class_data.get('classes', {}).items():
            for node in nodes:
                node_type_name = node.get('type')
                if not node_type_name or node_type_name in all_nodes: continue
                all_nodes[node_type_name] = {
                    "displayName": node.get('name', node_type_name),
                    "group": f"Class: {class_name}"
                }
        
        return {"node_types": all_nodes}
    except Exception as e:
        logging.error(f"Error fetching detailed node types resource: {e}", exc_info=True)
        return {"error": f"Error fetching detailed node types: {str(e)}", "status_code": 500}

@app.resource("n8n:/tags", description="Provides information on all n8n tags.")
async def get_tags_resource_data() -> dict[str, Any]:
    """
    Retrieves the complete list of tags defined in the n8n instance.
    
    This resource provides access to the system-wide tag registry, useful for
    workflow organization, filtering, and tag assignment operations. Each tag
    entry includes its unique identifier and display name.

    Returns:
        A dictionary containing tag information, or error data on failure.
        Success response structure:
        {
            "tags": [
                { "id": "tag-id-1", "name": "Production" },
                { "id": "tag-id-2", "name": "Development" },
                // Additional tags...
            ]
        }
        
        Error response structure:
        {
            "error": "Error description",
            "status_code": 500
        }
    """
    if not n8n_client:
        logging.error("get_tags_resource_data: n8n_client is not initialized.")
        return {"error": "n8n_client not initialized", "status_code": 500}
    try:
        tags_response = await n8n_client.list_tags()
        return {"tags": tags_response.get("data", [])}
    except Exception as e:
        logging.error(f"Error fetching tags resource: {e}", exc_info=True)
        return {"error": f"Error fetching tags: {str(e)}", "status_code": 500}
