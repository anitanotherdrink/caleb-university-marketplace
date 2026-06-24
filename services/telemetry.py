"""Lightweight telemetry (PRD §12). Emits structured snake_case events to the
application log. In production this would feed a metrics/analytics pipeline;
here it gives an auditable trail without ever logging secrets.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger("marketplace.telemetry")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

_SENSITIVE = {"password", "password_hash", "token", "token_hash"}


def emit(event: str, **props) -> None:
    safe = {k: v for k, v in props.items() if k not in _SENSITIVE}
    logger.info("event=%s %s", event, json.dumps(safe, default=str))
