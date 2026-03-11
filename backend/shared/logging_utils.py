import logging
from typing import Any, Optional


logger = logging.getLogger("resolution")


def log_resolution(component: str, workspace_id: Optional[str], source: str, details: Any = None) -> None:
    """
    Structured decision logging helper.
    Never pass secrets as `details`.
    """
    logger.info(
        "%s configuration resolved | workspace_id=%s | source=%s | details=%s",
        component,
        workspace_id,
        source,
        details,
    )

