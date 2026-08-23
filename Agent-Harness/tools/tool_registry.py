from tools.tools import (list_files_in_directory, read_file,
                          write_file, run_command, search)


TOOL_DESCRIPTION = {
    "list_files": {
        "description": "List files inside the target repo. Use '.' for the repo root.",
        "input_format": {"directory": "."},
    },
    "read_file": {
        "description": "Read a file inside the target repo.",
        "input_format": {"file_path": "src/example.py"},
    },
    "write_file": {
        "description": "Replace the full contents of an existing file inside the target repo.",
        "input_format": {"file_path": "src/example.py", "content": "<new full file content>"},
    },
    "run_command": {
        "description": "Run pytest inside the target repo. Only python3 -m pytest with optional repo-internal paths is allowed.",
        "input_format": {"command": "python3 -m pytest"},
    },
    "search": {
        "description": "Search for text inside files in the target repo.",
        "input_format": {"pattern": "<text_to_search_for>"},
    },
}

TOOLS = {
    "list_files": list_files_in_directory,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search": search
}


def run_tools(tool_name:str,tool_input: dict, workspace_path=None):
    """
    Run a tool by name with the provided input.

    Args:
        tool_name (str): The name of the tool to run.
        tool_input (dict): The input for the tool.
    """
    if tool_name not in TOOLS:
        return {
            "output": None,
            "error": f"Tool '{tool_name}' not found.",
            "success": False,
        }

    if workspace_path is not None:
        tool_input = dict(tool_input)
        tool_input["workspace_path"] = workspace_path

    # try:
    result = TOOLS[tool_name](**tool_input)
    return result
    # except Exception as e:
    #     return {
    #         "output": None,
    #         "error": str(e),
    #         "success": False,
    #     }
