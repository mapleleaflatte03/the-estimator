"""UI language for messages a person reads. Set from the request's Accept-Language header."""
from __future__ import annotations

from contextvars import ContextVar

ui_language: ContextVar[str] = ContextVar("ui_language", default="vi")


def current_lang() -> str:
    return "en" if ui_language.get() == "en" else "vi"
