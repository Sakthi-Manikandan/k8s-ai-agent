from backend.ai.prompt_builder import build_system_prompt, build_investigation_prompt
from backend.ai.llm_client import call_ollama
from backend.core.logger import log


def analyze_investigation(investigation: dict) -> dict:
    """
    Takes K8s investigation data and returns AI diagnosis!
    """
    log.info("Starting AI reasoning...")

    # Build prompts
    system_prompt = build_system_prompt()
    user_prompt = build_investigation_prompt(investigation)

    # Call Ollama
    result = call_ollama(system_prompt, user_prompt)

    if not result["success"]:
        return {
            "success": False,
            "error": result.get("error")
        }

    return {
        "success": True,
        "diagnosis": result["diagnosis"]
    }
