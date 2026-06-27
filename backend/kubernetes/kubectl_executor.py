import subprocess
from backend.core.logger import log


def execute_kubectl(command: list) -> dict:
    """
    Safely executes kubectl commands and returns structured output.
    """
    try:
        log.info(f"Executing kubectl command: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            log.info("kubectl command executed successfully")
            return {
                "success": True,
                "output": result.stdout.strip(),
                "error": None
            }

        log.error(f"kubectl command failed: {result.stderr}")
        return {
            "success": False,
            "output": None,
            "error": result.stderr.strip()
        }

    except subprocess.TimeoutExpired:
        log.error("kubectl command timed out")
        return {
            "success": False,
            "output": None,
            "error": "Command timed out after 30 seconds"
        }

    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        return {
            "success": False,
            "output": None,
            "error": str(e)
        }