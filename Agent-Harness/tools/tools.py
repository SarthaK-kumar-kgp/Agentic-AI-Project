from pathlib import Path
import difflib
import shlex
import subprocess
import sys

TARGET_REPO = Path(__file__).resolve().parents[1] / "fixtures" / "sample_python_repo"


def get_target_root(workspace_path=None):
    if workspace_path is None:
        return TARGET_REPO.resolve()
    return Path(workspace_path).resolve()


def is_inside_root(path, root):
    return path == root or root in path.parents


def should_skip_path(path):
    skipped_dirs = {".pytest_cache", "__pycache__", ".git"}
    if path.suffix == ".pyc":
        return True
    for part in path.parts:
        if part in skipped_dirs:
            return True
    return False


def list_files_in_directory(directory: str = ".", workspace_path=None):
    """
    List all files in a directory and its subdirectories.
    Args:
        directory (str): A path inside the target repo.
    """
    target_root = get_target_root(workspace_path)
    requested_path = (target_root / directory).resolve()

    if not is_inside_root(requested_path, target_root):
        return {
            "output": [],
            "error": "Path is outside the target repo.",
            "success": False,
        }

    if not requested_path.exists():
        return {
            "output": [],
            "error": "Path does not exist.",
            "success": False,
        }

    files = []
    for path in requested_path.rglob("*"):
        if should_skip_path(path):
            continue
        if path.is_file():
            files.append(str(path.relative_to(target_root)))

    return {
        "output": sorted(files),
        "error": None,
        "success": True,
    }

def read_file(file_path: str, workspace_path=None):
    """
    Read the contents of a file.

    Args:
        file_path (str): A file path inside the target repo.
    """
    target_root = get_target_root(workspace_path)
    requested_path = (target_root / file_path).resolve()

    if not is_inside_root(requested_path, target_root):
        return {
            "output": None,
            "error": "Path is outside the target repo.",
            "success": False,
        }

    if not requested_path.exists():
        return {
            "output": None,
            "error": "File does not exist.",
            "success": False,
        }

    if not requested_path.is_file():
        return {
            "output": None,
            "error": "Path is not a file.",
            "success": False,
        }

    content = requested_path.read_text(encoding="utf-8")
    return {
        "output": content,
        "error": None,
        "success": True,
    }
    
def write_file(file_path:str,content:str, workspace_path=None):
    """
    Write content to a file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to write to the file.
    """
    target_root = get_target_root(workspace_path)
    requested_path = (target_root / file_path).resolve()
    
    if not is_inside_root(requested_path, target_root):
        return {
            "output": None,
            "error": "Path is outside the target repo.",
            "success": False,
        }

    if not requested_path.exists():
        return {
            "output": None,
            "error": "File does not exist.",
            "success": False,
        }

    if not requested_path.is_file():
        return {
            "output": None,
            "error": "Path is not a file.",
            "success": False,
        }
    if content is None:
        return {
            "output": None,
            "error": "Content cannot be None.",
            "success": False,
        }

    old_content = requested_path.read_text(encoding="utf-8")
    requested_path.write_text(content, encoding="utf-8")
    old_lines = old_content.splitlines(keepends=True)
    new_lines = content.splitlines(keepends=True)

    difference_lines = difflib.unified_diff(
                        old_lines, 
                        new_lines)
    file_difference = "".join(difference_lines)
    return {
        "output": {
            "file_name": str(requested_path.relative_to(target_root)),
            "file_start_text": old_content,
            "file_end_text": content,
            "file_difference": file_difference,
        },
        "error": None,
        "success": True,
    }

def run_command(command:str, workspace_path=None):
    """
    Run a shell command and return its output.

    Args:
        command (str): The command to run.
    """
    command_parts = shlex.split(command)

    if command_parts[:3] != ["python3", "-m", "pytest"]:
        return {
            "output": None,
            "error": "Command is not allowed.",
            "success": False,
        }

    target_root = get_target_root(workspace_path)
    for path_arg in command_parts[3:]:
        if path_arg.startswith("-"):
            return {
                "output": None,
                "error": "Pytest flags are not allowed yet.",
                "success": False,
            }

        requested_path = (target_root / path_arg).resolve()
        if requested_path != target_root and target_root not in requested_path.parents:
            return {
                "output": None,
                "error": "Pytest path is outside the target repo.",
                "success": False,
            }

    try:
        command_parts[0] = sys.executable
        output = subprocess.run(
            command_parts,
            cwd=target_root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "output": None,
            "error": "Command timed out.",
            "success": False,
        }

    return {
        "output": {
            "stdout": output.stdout,
            "stderr": output.stderr,
            "exit_code": output.returncode
        },
        "error": None,
        "success": output.returncode == 0
    }

def search(pattern: str, workspace_path=None):
    """
    Search for a text pattern inside files in the target repo.

    Args:
        pattern (str): The text to search for.
    """
    target_root = get_target_root(workspace_path)

    if not isinstance(pattern, str):
        return {
            "output": [],
            "error": "pattern must be a string.",
            "success": False,
        }

    if pattern == "":
        return {
            "output": [],
            "error": "pattern cannot be empty.",
            "success": False,
        }

    matches = []
    for path in target_root.rglob("*"):
        if should_skip_path(path):
            continue
        if not path.is_file():
            continue

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            if pattern in line:
                matches.append(
                    {
                        "file_name": str(path.relative_to(target_root)),
                        "line_number": line_number,
                        "line": line,
                    }
                )

    return {
        "output": matches,
        "error": None,
        "success": True,
    }
    
