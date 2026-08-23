from tools.tools import (list_files_in_directory, read_file,
                          write_file, run_command, search)
TOOLS = {
    "list_files": list_files_in_directory,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search": search
}


def run_tools(tool_name:str,tool_input: dict):
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

    # try:
    result = TOOLS[tool_name](**tool_input)
    return result
    # except Exception as e:
    #     return {
    #         "output": None,
    #         "error": str(e),
    #         "success": False,
    #     }