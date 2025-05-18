'''
Defines MCP tools for interacting with n8n nodes.
'''
import logging
import json
import os
from typing import Any, Optional

from mcp_server import app
from config import (
    n8n_client, CATEGORY_CLASSIFICATION_FILE_PATH, CLASS_CLASSIFICATION_FILE_PATH, 
    NODE_DATA_BASE_PATH, NODE_CATEGORIES_PATH_BASE, NODE_CLASSES_PATH_BASE
)

def _find_class_for_node_type(node_type_to_find: str, class_data_dict: dict[str, Any]) -> Optional[str]:
    """Find the class name for a given node type."""
    if not node_type_to_find or not class_data_dict or 'classes' not in class_data_dict:
        return None
    for class_key, nodes_in_class in class_data_dict.get('classes', {}).items():
        for node in nodes_in_class:
            if node.get('type', '').lower() == node_type_to_find.lower():
                return class_key
    return None

def _find_category_for_node_type(node_type_to_find: str, category_data_dict: dict[str, Any]) -> Optional[str]:
    """Find the category name for a given node type."""
    if not node_type_to_find or not category_data_dict or 'categories' not in category_data_dict:
        return None
    for cat_key, nodes_in_cat in category_data_dict.get('categories', {}).items():
        for node in nodes_in_cat:
            if node.get('type', '').lower() == node_type_to_find.lower():
                return cat_key
    return None

@app.tool()
async def list_nodes(
    category: Optional[str] = None,
    node_class: Optional[str] = None, 
    return_types_only: bool = True
) -> dict[str, Any]:
    """
    Retrieves available node types from the local classification system with optional filtering.
    
    This operation provides access to the node type registry, allowing discovery of available
    processing components for workflow construction. Results can be filtered by functional 
    category (e.g., 'Core Nodes', 'Analytics') and/or node class (e.g., 'trigger', 'action').
    The operation queries local classification files rather than the n8n API directly.
    """
    logging.info(f"list_nodes called with category={category}, node_class={node_class}, return_types_only={return_types_only}")
    try:
        category_data: dict[str, Any] = {}
        class_data: dict[str, Any] = {}

        if os.path.exists(CATEGORY_CLASSIFICATION_FILE_PATH):
            with open(CATEGORY_CLASSIFICATION_FILE_PATH, 'r', encoding='utf-8') as f:
                category_data = json.load(f)
        else:
            logging.warning(f"Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}")
            return {"status": "failure", "message": f"Category classification file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}", "count": 0, "nodes": []}

        if os.path.exists(CLASS_CLASSIFICATION_FILE_PATH):
            with open(CLASS_CLASSIFICATION_FILE_PATH, 'r', encoding='utf-8') as f:
                class_data = json.load(f)
        else:
            logging.warning(f"Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}")
            return {"status": "failure", "message": f"Class classification file not found: {CLASS_CLASSIFICATION_FILE_PATH}", "count": 0, "nodes": []}

        normalized_category_filter: Optional[str] = category.lower() if category else None
        normalized_class_filter: Optional[str] = node_class.lower() if node_class else None
        
        result_nodes_details: list[dict[str, Any]] = []
        
        if normalized_category_filter and normalized_class_filter:
            target_category_key = next((ck for ck in category_data.get('categories', {}).keys() if ck.lower() == normalized_category_filter), None)
            target_class_key = next((clk for clk in class_data.get('classes', {}).keys() if clk.lower() == normalized_class_filter), None)

            if target_category_key and target_class_key:
                nodes_in_category = category_data['categories'][target_category_key]
                for node_info_cat in nodes_in_category:
                    node_type_cat = node_info_cat.get('type')
                    if not node_type_cat: continue
                    if any(node_info_cls.get('type', '').lower() == node_type_cat.lower() for node_info_cls in class_data['classes'][target_class_key]):
                        result_nodes_details.append({
                            "node_name_folder": node_info_cat.get('path'), 
                            "display_name": node_info_cat.get('name'),
                            "type_identifier": node_type_cat, 
                            "source_type": "combined",
                            "group_name": f"{target_category_key} & {target_class_key}",
                            "category": target_category_key, 
                            "class": target_class_key
                        })
        elif normalized_category_filter:
            target_category_key = next((ck for ck in category_data.get('categories', {}).keys() if ck.lower() == normalized_category_filter), None)
            if target_category_key:
                for node_info in category_data['categories'][target_category_key]:
                    node_type = node_info.get('type')
                    if not node_type: continue
                    result_nodes_details.append({
                        "node_name_folder": node_info.get('path'), 
                        "display_name": node_info.get('name'),
                        "type_identifier": node_type, 
                        "source_type": "category", 
                        "group_name": target_category_key,
                        "category": target_category_key, 
                        "class": _find_class_for_node_type(node_type, class_data)
                    })
        elif normalized_class_filter:
            target_class_key = next((clk for clk in class_data.get('classes', {}).keys() if clk.lower() == normalized_class_filter), None)
            if target_class_key:
                for node_info in class_data['classes'][target_class_key]:
                    node_type = node_info.get('type')
                    if not node_type: continue
                    result_nodes_details.append({
                        "node_name_folder": node_info.get('path'), 
                        "display_name": node_info.get('name'),
                        "type_identifier": node_type, 
                        "source_type": "class", 
                        "group_name": target_class_key,
                        "class": target_class_key, 
                        "category": _find_category_for_node_type(node_type, category_data)
                    })
        else: # No filters
            all_nodes_map: dict[str, dict[str, Any]] = {}
            for cat_key, nodes_in_cat_list in category_data.get('categories', {}).items():
                for node in nodes_in_cat_list:
                    node_type = node.get('type')
                    if node_type and node_type not in all_nodes_map:
                        all_nodes_map[node_type] = {
                            "node_name_folder": node.get('path'), 
                            "display_name": node.get('name'),
                            "type_identifier": node_type, 
                            "source_type": "category", 
                            "group_name": cat_key,
                            "category": cat_key, 
                            "class": _find_class_for_node_type(node_type, class_data)
                        }
            for cls_key, nodes_in_cls_list in class_data.get('classes', {}).items():
                for node in nodes_in_cls_list:
                    node_type = node.get('type')
                    if node_type:
                        if node_type not in all_nodes_map:
                            all_nodes_map[node_type] = {
                                "node_name_folder": node.get('path'), 
                                "display_name": node.get('name'),
                                "type_identifier": node_type, 
                                "source_type": "class", 
                                "group_name": cls_key,
                                "category": _find_category_for_node_type(node_type, category_data), 
                                "class": cls_key
                            }
                        elif not all_nodes_map[node_type].get("class"):
                            all_nodes_map[node_type]["class"] = cls_key
            result_nodes_details = list(all_nodes_map.values())

        if return_types_only:
            node_list_content = [node.get("type_identifier") for node in result_nodes_details if node.get("type_identifier")]
        else:
            node_list_content = result_nodes_details
        
        final_response = {"status": "success", "count": len(node_list_content), "nodes": node_list_content}
        logging.debug(f"list_nodes response: {json.dumps(final_response, ensure_ascii=False, indent=2)[:500]}...")
        return final_response

    except FileNotFoundError as e:
        logging.error(f"Node classification file not found during list_nodes: {e.filename}", exc_info=True)
        return {"status": "failure", "message": f"Error: A required node classification file was not found ({e.filename}).", "count": 0, "nodes": []}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from a node classification file during list_nodes: {e}", exc_info=True)
        return {"status": "failure", "message": "Error: Failed to parse a node classification file. File might be corrupted.", "count": 0, "nodes": []}
    except Exception as e:
        logging.error(f"Unexpected error in list_nodes: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to list nodes: {str(e)}", "count": 0, "nodes": []}

@app.tool()
async def get_node_info(node_type: str) -> dict[str, Any]:
    """
    Retrieves comprehensive definition information for a specific node type.
    
    This operation provides detailed technical specifications for a requested node type,
    including configuration schema, parameters, and implementation details. It returns 
    the content of all definition files associated with the node, enabling thorough
    analysis of node capabilities and required configuration.
    
    The operation queries local node definition files rather than the n8n API directly,
    accessing the complete set of files that define the node's behavior and interface.
    
    Note:
        The returned files typically include:
        - '*.node.json': Core node registration information
        - '*.description.ts' or '/descriptions/*.ts': Parameter definitions and UI schema
        - '*.node.ts' or '*.node.js': Implementation code
        - Test files and examples when available
    """
    logging.info(f"get_node_info called for node_type: {node_type}")
    try:
        normalized_node_type: str = node_type.lower()
        category_data: dict[str, Any] = {}
        class_data: dict[str, Any] = {}

        if os.path.exists(CATEGORY_CLASSIFICATION_FILE_PATH):
            with open(CATEGORY_CLASSIFICATION_FILE_PATH, 'r', encoding='utf-8') as f: 
                category_data = json.load(f)
        else: 
            return {"status": "failure", "message": f"Category file not found: {CATEGORY_CLASSIFICATION_FILE_PATH}"}
        
        if os.path.exists(CLASS_CLASSIFICATION_FILE_PATH):
            with open(CLASS_CLASSIFICATION_FILE_PATH, 'r', encoding='utf-8') as f: 
                class_data = json.load(f)
        else: 
            return {"status": "failure", "message": f"Class file not found: {CLASS_CLASSIFICATION_FILE_PATH}"}

        found_node_info: Optional[dict[str, Any]] = None
        source_type_origin: Optional[str] = None
        group_name_origin: Optional[str] = None

        for cat_name, nodes in category_data.get('categories', {}).items():
            for node_detail in nodes:
                if node_detail.get('type', '').lower() == normalized_node_type:
                    found_node_info, source_type_origin, group_name_origin = node_detail, 'category', cat_name
                    break
            if found_node_info: 
                break
        
        if not found_node_info:
            for class_name, nodes in class_data.get('classes', {}).items():
                for node_detail in nodes:
                    if node_detail.get('type', '').lower() == normalized_node_type:
                        found_node_info, source_type_origin, group_name_origin = node_detail, 'class', class_name
                        break
                if found_node_info: 
                    break

        if not found_node_info:
            logging.warning(f"Node type '{node_type}' not found in classification files.")
            return {"status": "failure", "message": f"Node type not found: {node_type}"}

        node_name_folder: Optional[str] = found_node_info.get('path')
        if not node_name_folder:
            logging.error(f"Node '{node_type}' found but 'path' (node_name_folder) is missing.")
            return {"status": "failure", "message": f"Node path (node_name_folder) not found for {node_type}"}

        base_path_for_node: str = NODE_CATEGORIES_PATH_BASE if source_type_origin == 'category' else NODE_CLASSES_PATH_BASE
        if not group_name_origin or not isinstance(group_name_origin, str):
            logging.error(f"Invalid group name '{group_name_origin}' for node {node_type}")
            return {"status": "failure", "message": f"Invalid group for node {node_type}"}
            
        node_folder_full_path: str = os.path.join(base_path_for_node, group_name_origin, node_name_folder)
        
        logging.info(f"Attempting to read node files from: {node_folder_full_path}")
        if not os.path.exists(node_folder_full_path) or not os.path.isdir(node_folder_full_path):
            logging.error(f"Node data folder does not exist or is not a directory: {node_folder_full_path}")
            return {"status": "failure", "message": f"Node data folder not found: {node_folder_full_path}"}
            
        file_contents_map: dict[str, str] = {}
        for item_in_folder in os.listdir(node_folder_full_path):
            item_path = os.path.join(node_folder_full_path, item_in_folder)
            if os.path.isfile(item_path):
                try:
                    with open(item_path, 'r', encoding='utf-8') as f_content:
                        file_contents_map[item_in_folder] = f_content.read()
                except Exception as e_read:
                    logging.warning(f"Error reading file {item_path}: {e_read}")
                    file_contents_map[item_in_folder] = f"Error reading file: {str(e_read)}"
        
        return {
            "status": "success",
            "type_identifier": found_node_info.get('type'),
            "display_name": found_node_info.get('name'),
            "source_type": source_type_origin,
            "group_name": group_name_origin,
            "node_name_folder": node_name_folder,
            "files": file_contents_map
        }

    except FileNotFoundError as e:
        logging.error(f"A classification file was not found during get_node_info for {node_type}: {e.filename}", exc_info=True)
        return {"status": "failure", "message": f"Error: Node classification file missing ({e.filename})."}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from a classification file during get_node_info for {node_type}: {e}", exc_info=True)
        return {"status": "failure", "message": "Error: Failed to parse a node classification file. File might be corrupted."}
    except Exception as e:
        logging.error(f"Unexpected error in get_node_info for {node_type}: {e}", exc_info=True)
        return {"status": "failure", "message": f"Failed to get node info: {str(e)}"} 