"""Integration modules for external APIs."""

from .gemini import GeminiClient
from .claude import ClaudeClient
from .nanobanana import NanoBananaClient
from .email import EmailClient

__all__ = ["GeminiClient", "ClaudeClient", "NanoBananaClient", "EmailClient"]
