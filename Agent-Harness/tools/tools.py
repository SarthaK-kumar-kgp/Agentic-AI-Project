from pathlib import Path
import difflib

TARGET_REPO = Path(__file__).resolve().parents[1] / "fixtures" / "sample_python_repo"


def list_files_in_directory(directory: str = "."):
    """
    List all files in a directory and its subdirectories.
    Args:
        directory (str): A path inside the target repo.
    """
    target_root = TARGET_REPO.resolve()
    requested_path = (target_root / directory).resolve()

    if not str(requested_path).startswith(str(target_root)):
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
        if path.is_file():
            files.append(str(path.relative_to(target_root)))

    return {
        "output": sorted(files),
        "error": None,
        "success": True,
    }

def read_file(file_path: str):
    """
    Read the contents of a file.

    Args:
        file_path (str): A file path inside the target repo.
    """
    target_root = TARGET_REPO.resolve()
    requested_path = (target_root / file_path).resolve()

    if not str(requested_path).startswith(str(target_root)):
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
    
def write_file(file_path:str,content:str):
    """
    Write content to a file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to write to the file.
    """
    target_root = TARGET_REPO.resolve()
    requested_path = (target_root / file_path).resolve()
    
    if not str(requested_path).startswith(str(target_root)):
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

def run_command(command:str):
    """
    Run a shell command and return its output.

    Args:
        command (str): The command to run.
    """
    return None 

def search(file_list:list, pattern:str):
    """
    Search for files in a directory and its subdirectories that match a given pattern.

    Args:
        file_list (list): A list of file paths.
        pattern (str): The pattern to match (e.g., '*.txt').
    """
    return [file for file in file_list if pattern in str(file)]



