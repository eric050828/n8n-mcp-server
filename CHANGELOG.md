# Changelog

This file documents all significant changes to the n8n MCP Server project.

## [0.1.0] - 2025-05-19

### Features
- **Workflow Management Features**
  - `list_workflows`: List workflows with filtering capabilities
  - `get_workflow`: Retrieve detailed workflow definitions
  - `create_workflow`: Create new workflows with nodes, connections, settings, and static data
  - `update_workflow`: Update existing workflows (name, nodes, connections, activation status, settings, static data)
  - `delete_workflow`: Delete workflows
  - `activate_workflow`: Activate workflows
  - `deactivate_workflow`: Deactivate workflows
- **Node Discovery & Analysis Features**
  - `list_nodes`: List available node types from local classification files (filtered by category/class)
  - `get_node_info`: Retrieve detailed node definition files for a specific node type
- **Execution Monitoring Features**
  - `list_workflow_executions`: List workflow execution records with filtering
  - `get_execution`: Get detailed information for a specific execution
  - `delete_execution`: Delete execution records
- **MCP Resources**
  - `n8n:/workflow/{workflow_id}`: Access workflow definition data
  - `n8n:/node-types`: Access information on available n8n node types from local files
  - `n8n:/tags`: Access information on all n8n tags