'''
Defines MCP tools for interacting with n8n workflow executions.
'''
import logging
from typing import Any, Optional

from mcp_server import app
from config import n8n_client
from n8n_sdk_python.models.executions import ExecutionList, Execution, ExecutionStatus

@app.tool()
async def list_workflow_executions(
    workflow_id: str, 
    status: Optional[str] = None,
    limit: int = 10,
    include_data: bool = False
) -> dict[str, Any]:
    """
    Retrieves execution history records for a specified workflow with optional filtering.
    
    This operation returns a paginated list of execution records for a given workflow,
    with the ability to filter by execution status(e.g. 'error', 'success', or 'waiting') and limit result size. Each record 
    contains execution metadata such as start/end times, status, and execution mode.
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        # Convert string status to ExecutionStatus enum if provided
        execution_status = None
        if status:
            try:
                execution_status = ExecutionStatus(status.lower())
            except ValueError:
                logging.warning(f"Invalid execution status: {status}. Using default.")
        
        result: ExecutionList = await n8n_client.list_executions(
            workflow_id=workflow_id,
            status=execution_status,
            limit=limit,
            include_data=include_data
        )
        
        executions: list[dict[str, Any]] = []
        if result.data:
            for exec_data in result.data:
                executions.append({
                    "id": exec_data.id,
                    "status": "success" if exec_data.finished and not hasattr(exec_data, "error") 
                             else ("running" if not exec_data.finished else "error"),
                    "started_at": exec_data.startedAt.isoformat() if exec_data.startedAt else None,
                    "finished_at": exec_data.stoppedAt.isoformat() if exec_data.stoppedAt else None,
                    "mode": exec_data.mode
                })
        
        return {
            "status": "success",
            "count": len(executions),
            "executions": executions
        }
    except Exception as e:
        logging.error(f"Error listing executions for workflow {workflow_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to list workflow executions: {str(e)}"}

@app.tool()
async def get_execution(
    execution_id: str, 
    include_data: bool = False
) -> dict[str, Any]:
    """
    Retrieves detailed information about a specific workflow execution.
    
    This operation returns comprehensive execution details including workflow context,
    execution timestamps, state, and optionally the complete execution data containing
    node inputs/outputs and error information.
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        execution: Execution = await n8n_client.get_execution(
            execution_id=execution_id,
            include_data=include_data
        )
        
        return {
            "status": "success",
            "execution": execution.model_dump(exclude_none=True)
        }
    except Exception as e:
        logging.error(f"Error getting execution {execution_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to get execution: {str(e)}"}

@app.tool()
async def delete_execution(execution_id: str) -> dict[str, Any]:
    """
    Permanently removes an execution record from the system.
    
    This operation deletes a specific execution record identified by its unique ID.
    Once deleted, execution data cannot be recovered. This is useful for removing 
    test executions, cleaning up execution history, or managing storage constraints.
    """
    if not n8n_client:
        return {"status": "failure", "message": "n8n_client is not initialized."}
    try:
        execution: Execution = await n8n_client.delete_execution(execution_id=execution_id)
        
        return {
            "status": "success",
            "message": f"Execution {execution_id} deleted successfully."
        }
    except Exception as e:
        logging.error(f"Error deleting execution {execution_id}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to delete execution: {str(e)}"} 