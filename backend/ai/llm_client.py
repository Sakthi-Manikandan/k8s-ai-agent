import httpx
import json
from backend.core.settings import settings
from backend.core.logger import log


def call_ollama(system_prompt: str, user_prompt: str) -> dict:
    """
    Sends prompt to Ollama and gets AI response back.
    Like asking a question to a Senior SRE!
    """
    log.info(f"Calling Ollama with model: {settings.OLLAMA_MODEL}")

    # Build the request payload
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "stream": False,    # Get complete response at once
        "format": "json"    # Force JSON response
    }

    try:
        # Call Ollama API
        with httpx.Client(timeout=120.0) as client:
            log.info("Sending request to Ollama...")

            response = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload
            )

            # Check if request was successful
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            # Extract the message content
            content = response_data.get(
                "message", {}
            ).get("content", "")

            log.info("Received response from Ollama!")

            # Parse JSON response from LLM
            try:
                diagnosis = json.loads(content)
                return {
                    "success": True,
                    "diagnosis": diagnosis
                }
            except json.JSONDecodeError:
                log.warning(
                    "LLM response was not valid JSON "
                    "trying to extract..."
                )
                return {
                    "success": True,
                    "diagnosis": {
                        "root_cause": "Analysis complete",
                        "explanation": content,
                        "suggested_fix": "See explanation above",
                        "kubectl_commands": [],
                        "prevention": "Monitor cluster regularly",
                        "confidence": 70
                    }
                }

    except httpx.TimeoutException:
        log.error("Ollama request timed out after 120 seconds")
        return {
            "success": False,
            "error": "AI request timed out. "
                     "Try again or check Ollama is running!"
        }

    except httpx.ConnectError:
        log.error("Cannot connect to Ollama!")
        return {
            "success": False,
            "error": "Cannot connect to Ollama. "
                     "Make sure Ollama is running on "
                     "http://localhost:11434"
        }

    except Exception as e:
        log.error(f"Unexpected error calling Ollama: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }