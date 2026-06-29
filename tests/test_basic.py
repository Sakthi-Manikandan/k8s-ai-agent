"""
Basic tests for K8s AI Agent
"""


def test_settings_load():
    """Test that settings load correctly"""
    from backend.core.settings import settings
    assert settings.APP_ENV is not None
    assert settings.OLLAMA_MODEL is not None
    assert settings.APP_PORT == 8000


def test_logger_setup():
    """Test that logger sets up correctly"""
    from backend.core.logger import log
    assert log is not None


def test_kubectl_executor_exists():
    """Test that kubectl executor is importable"""
    from backend.kubernetes.kubectl_executor import execute_kubectl
    assert execute_kubectl is not None


def test_investigation_service_exists():
    """Test that investigation service is importable"""
    from backend.kubernetes.investigation_service import run_investigation
    assert run_investigation is not None


def test_ai_reasoning_exists():
    """Test that AI reasoning engine is importable"""
    from backend.ai.reasoning_engine import analyze_investigation
    assert analyze_investigation is not None


def test_agent_service_exists():
    """Test that agent service is importable"""
    from backend.services.agent_service import run_full_agent_pipeline
    assert run_full_agent_pipeline is not None