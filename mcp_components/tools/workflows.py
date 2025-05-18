'''
Defines MCP tools for interacting with n8n workflows.
'''
import logging
from typing import Any, Optional

from mcp_server import app
from config import n8n_client
from n8n_sdk_python.models.workflows import (
    Workflow, WorkflowList, Node, Connection, 
    WorkflowSettings, WorkflowStaticData
)

@app.tool()
async def list_workflows(
    active_only: bool = False, 
    tags: Optional[str] = None,
    name: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: Optional[int] = None
) -> dict[str, Any]:
    """
    Retrieves a filtered list of workflows from the n8n instance.
    
    This operation returns a collection of workflow summaries matching the specified filter criteria.
    Each workflow summary includes basic metadata such as ID, name, active status, and associated tags,
    but not the complete workflow definition (use get_workflow for full details).
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        params: dict[str, Any] = {}
        if active_only:
            params["active"] = True
        if tags:
            params["tags"] = tags
        if name:
            params["name"] = name
        if project_id:
            params["project_id"] = project_id
        if limit:
            params["limit"] = limit
        
        result: WorkflowList = await n8n_client.list_workflows(**params)
        
        workflows: list[dict[str, Any]] = []
        if result.data:
            for wf in result.data:
                workflows.append({
                    "id": wf.id,
                    "name": wf.name,
                    "active": wf.active,
                    "created_at": wf.createdAt.isoformat() if wf.createdAt else None,
                    "updated_at": wf.updatedAt.isoformat() if wf.updatedAt else None,
                    "tags": [{"id": tag.id, "name": tag.name} for tag in wf.tags] if wf.tags else []
                })
                
        return {
            "status": "success",
            "count": len(workflows),
            "workflows": workflows
        }
    except Exception as e:
        logging.error(f"Error in list_workflows: {e}", exc_info=True)
        return {"status": "failure", "message": str(e)}

@app.tool()
async def get_workflow(
    workflow_id: str,
    exclude_pinned_data: bool = True
) -> dict[str, Any]:
    """
    Retrieves the complete definition of a specific workflow.
    
    This operation returns the full technical specification of the requested workflow,
    including all nodes, connections, settings, and metadata. If exclude_pinned_data is True,
    the response will not include the pinned data, it will reduce the response size,
    otherwise the response will include the complete pinned data.
        
    Note:
        The workflow object includes comprehensive information suitable for:
        - Analysis of workflow structure and functionality
        - Extraction of configuration patterns
        - Cloning or modification via the update_workflow operation
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        workflow: Workflow = await n8n_client.get_workflow(
            workflow_id=workflow_id,
            exclude_pinned_data=exclude_pinned_data
        )
        return {
            "status": "success",
            "workflow": workflow.model_dump(exclude_none=True)
        }
    except Exception as e:
        logging.error(f"Error in get_workflow for ID {workflow_id}: {e}", exc_info=True)
        return {"status": "failure", "message": str(e)}

@app.tool()
async def create_workflow(
    name: str, 
    nodes: list[dict[str, Any]], 
    connections: Optional[dict[str, Any]] = None,
    active: bool = False,
    settings: Optional[dict[str, Any]] = None,
    static_data: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Creates a new workflow with the specified configuration.
    
    This operation constructs a complete workflow based on the provided parameters,
    creating both the workflow container and its internal processing logic. The 
    workflow structure must adhere to the n8n_sdk_python.models.workflows.WorkflowCreate
    model specification.
    
    Args:
        name: Display name for the workflow. Should be descriptive and unique for easy identification.
        nodes: Array of node configuration objects defining the processing steps.
              Each node must conform to the n8n_sdk_python.models.workflows.Node model.
        connections: Object defining data flow between nodes. Maps source nodes to target nodes
                    with specific connection types and indices. If omitted, creates a workflow
                    with disconnected nodes.
        active: Whether to activate the workflow upon creation. When True, the workflow
               becomes operational and can be triggered immediately after creation.
               Default is False (inactive).
        settings: Workflow execution configuration including timeout, data retention policies,
                 and timezone. If omitted, uses n8n system defaults.
        static_data: Persistent state storage for the workflow. Useful for tracking counters,
                    timestamps, or other state between executions. If omitted, initializes
                    with empty state.
    
    Returns:
        A structured response containing:
        - status: Operation result ('success' or 'failure')
        - message: Success confirmation or error description
        - workflow: Basic information about the created workflow (only present on success)
          - id: Unique identifier of the new workflow
          - name: Display name of the workflow
          - active: Current activation status
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        if connections is None:
            connections = {}
        if settings is None:
            settings = {
                "saveExecutionProgress": True,
                "saveManualExecutions": True,
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "executionTimeout": 3600,
                "timezone": "UTC"
            }
        
        workflow: Workflow = await n8n_client.create_workflow(
            name=name,
            nodes=nodes,
            connections=connections,
            settings=settings,
            static_data=static_data
        )
        # NOTE: N8n API is not allow to activate workflow immediately after creation.
        #       We need to activate it manually.
        
        if active and workflow and hasattr(workflow, 'id'):
            activated_workflow: Workflow = await n8n_client.activate_workflow(workflow_id=workflow.id)
            workflow.active = activated_workflow.active
        
        return {
            "status": "success",
            "message": f"Workflow '{name}' created successfully.",
            "workflow": {
                "id": workflow.id if workflow else None,
                "name": workflow.name if workflow else name,
                "active": workflow.active if workflow and hasattr(workflow, 'active') else active
            }
        }
    except Exception as e:
        logging.error(f"Error creating workflow '{name}': {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to create workflow: {str(e)}"}

@app.tool()
async def update_workflow(
    workflow_id: str,
    name: Optional[str] = None,
    nodes: Optional[list[dict[str, Any]]] = None,
    connections: Optional[dict[str, Any]] = None,
    active: Optional[bool] = None,
    settings: Optional[dict[str, Any]] = None,
    static_data: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Modifies an existing workflow with the specified configuration changes.
    
    This operation updates a workflow's structure, settings, or activation state.
    Only the parameters provided will be modified; omitted parameters retain their
    current values. The operation follows an atomic update pattern - retrieving
    the current workflow, applying changes, and submitting the complete updated
    workflow.
    
    Args:
        workflow_id: The unique identifier of the workflow to modify.
        name: New display name for the workflow. If omitted, retains current name.
        nodes: New array of node configuration objects. If provided, replaces ALL existing nodes.
              Each node must conform to the n8n_sdk_python.models.workflows.Node model.
        connections: New data flow configuration. If provided, replaces ALL existing connections.
        active: New activation state. If True, activates the workflow. If False, deactivates it.
                If omitted, maintains current activation state.
        settings: New execution configuration. If provided, updates workflow settings.
                 Partial updates are applied to the existing settings object.
        static_data: New persistent state storage. If provided, replaces the entire static data object.
                    To update specific fields, retrieve current static data first, then modify.
    
    Returns:
        A structured response containing:
        - status: Operation result ('success' or 'failure')
        - message: Success confirmation or error description
        - workflow: Basic information about the updated workflow (only present on success)
          - id: Workflow identifier
          - name: Current display name (updated if changed)
          - active: Current activation status (updated if changed)
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    logging.info(f"Attempting to update workflow ID: {workflow_id}")
    
    try:
        original_workflow: Workflow = await n8n_client.get_workflow(workflow_id=workflow_id)
        logging.info(f"Fetched original workflow: {original_workflow.name}, Active: {original_workflow.active}")
        
        update_name = name if name is not None else original_workflow.name
        update_nodes = nodes if nodes is not None else original_workflow.nodes
        update_connections = connections if connections is not None else original_workflow.connections
        update_settings = settings if settings is not None else (original_workflow.settings.model_dump() if original_workflow.settings else {})
        update_static_data = static_data if static_data is not None else original_workflow.staticData
        
        updated_workflow: Workflow = await n8n_client.update_workflow(
            workflow_id=workflow_id,
            name=update_name,
            nodes=update_nodes,
            connections=update_connections,
            settings=update_settings,
            static_data=update_static_data
        )
        logging.info(f"Workflow '{updated_workflow.name}' data updated via API.")

        final_active_status = original_workflow.active
        if hasattr(updated_workflow, 'active'):
             final_active_status = updated_workflow.active

        if active is not None and active != final_active_status:
            if active:
                logging.info(f"Activating workflow {workflow_id}...")
                activated_workflow: Workflow = await n8n_client.activate_workflow(workflow_id=workflow_id)
                final_active_status = activated_workflow.active
                logging.info(f"Workflow {workflow_id} activated.")
            else:
                logging.info(f"Deactivating workflow {workflow_id}...")
                deactivated_workflow: Workflow = await n8n_client.deactivate_workflow(workflow_id=workflow_id)
                final_active_status = deactivated_workflow.active
                logging.info(f"Workflow {workflow_id} deactivated.")
        
        return {
            "status": "success",
            "message": f"Workflow '{update_name}' updated successfully.",
            "workflow": {
                "id": updated_workflow.id,
                "name": updated_workflow.name,
                "active": final_active_status
            }
        }
    except Exception as e:
        logging.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to update workflow: {str(e)}"}

@app.tool()
async def delete_workflow(workflow_id: str) -> dict[str, Any]:
    """
    Permanently removes a workflow from the system.
    
    This operation deletes a workflow and all its associated configuration, including
    nodes, connections, and settings. This action is irreversible; once deleted, a
    workflow cannot be recovered without manual recreation.
    
    Active workflows are automatically deactivated before deletion.
    
    Args:
        workflow_id: The unique identifier of the workflow to delete.
    
    Returns:
        A structured response containing:
        - status: Operation result ('success' or 'failure')
        - message: Success confirmation or error description
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        workflow: Workflow = await n8n_client.get_workflow(workflow_id=workflow_id)
        workflow_name = workflow.name
        
        deleted_workflow: Workflow = await n8n_client.delete_workflow(workflow_id=workflow_id)
        logging.info(f"Workflow '{deleted_workflow.name}' (ID: {workflow_id}) deleted successfully.")
        return {
            "status": "success",
            "message": f"Workflow '{workflow_name}' (ID: {workflow_id}) deleted successfully."
        }
    except Exception as e:
        logging.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to delete workflow: {str(e)}"}

@app.tool()
async def activate_workflow(workflow_id: str) -> dict[str, Any]:
    """
    Enables a workflow for execution.
    
    This operation activates a workflow, making it operational and capable of processing
    data. Activation primarily affects trigger nodes within the workflow:
    - Webhook triggers become accessible via their webhook URLs
    - Schedule triggers begin executing on their defined schedule
    - Event triggers start listening for their triggering events
    
    Args:
        workflow_id: The unique identifier of the workflow to activate.
    
    Returns:
        A structured response containing:
        - status: Operation result ('success' or 'failure')
        - message: Success confirmation or error description
        - workflow: Basic information about the activated workflow (only present on success)
          - id: Workflow identifier
          - name: Workflow name
          - active: New activation status (should be true on success)
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        workflow: Workflow = await n8n_client.activate_workflow(workflow_id=workflow_id)
        logging.info(f"Workflow '{workflow.name}' activated successfully.")
        return {
            "status": "success",
            "message": f"Workflow '{workflow.name}' activated successfully.",
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "active": workflow.active
            }
        }
    except Exception as e:
        logging.error(f"Error activating workflow {workflow_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to activate workflow: {str(e)}"}

@app.tool()
async def deactivate_workflow(workflow_id: str) -> dict[str, Any]:
    """
    Disables a workflow from executing.
    
    This operation deactivates a workflow, suspending its operational capabilities:
    - Webhook triggers stop responding to requests
    - Schedule triggers no longer execute on their defined schedule
    - Event triggers stop listening for triggering events
    
    Deactivation is typically used for maintenance, testing, or suspending workflows
    that are not currently needed but should be preserved for future use.
    
    Args:
        workflow_id: The unique identifier of the workflow to deactivate.
    
    Returns:
        A structured response containing:
        - status: Operation result ('success' or 'failure')
        - message: Success confirmation or error description
        - workflow: Basic information about the deactivated workflow (only present on success)
          - id: Workflow identifier
          - name: Workflow name
          - active: New activation status (should be false on success)
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        workflow: Workflow = await n8n_client.deactivate_workflow(workflow_id=workflow_id)
        logging.info(f"Workflow '{workflow.name}' deactivated successfully.")
        return {
            "status": "success",
            "message": f"Workflow '{workflow.name}' deactivated successfully.",
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "active": workflow.active
            }
        }
    except Exception as e:
        logging.error(f"Error deactivating workflow {workflow_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to deactivate workflow: {str(e)}"} 