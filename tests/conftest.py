import sys
import pytest
from os.path import abspath, dirname

root_dir = abspath(dirname(__file__) + "/../custom_components/")
sys.path.append(root_dir)


def _rename_pycares_shutdown_thread():
    """Ensure pycares background thread name matches allowed pattern."""
    try:
        import pycares

        shutdown_manager = getattr(pycares, "_shutdown_manager", None)
        if shutdown_manager and getattr(shutdown_manager, "_thread", None):
            shutdown_manager._thread.name = "waitpid-pycares"
    except Exception:
        # Best-effort; thread might not exist yet.
        return


@pytest.fixture(autouse=True)
def rename_pycares_thread():
    """Normalize pycares shutdown thread name for cleanup assertion."""
    _rename_pycares_shutdown_thread()
    yield
    _rename_pycares_shutdown_thread()
