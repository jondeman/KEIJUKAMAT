"""
Configuration management for KonseptiKeiju.

Uses pydantic-settings to load configuration from environment variables
with support for .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # API Keys
    # ==========================================================================
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    anthropic_api_key: str = Field(default="", description="Anthropic Claude API key")
    nanobanana_api_key: str = Field(default="", description="Nano Banana Pro API key")
    brandfetch_api_key: str = Field(default="", description="Brandfetch API key")

    # ==========================================================================
    # Email Configuration
    # ==========================================================================
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from_name: str = Field(default="KonseptiKeiju")
    sendgrid_api_key: str = Field(default="", description="SendGrid API key for email sending")
    sendgrid_from_email: str = Field(default="", description="SendGrid verified from email")
    resend_api_key: str = Field(default="", description="Resend API key for email sending")
    resend_from_email: str = Field(default="", description="Resend verified from email")

    # ==========================================================================
    # Application Settings
    # ==========================================================================
    access_code: str = Field(default="", description="Access code for authentication")
    base_url: str = Field(default="http://localhost:8000")
    delivery_base_url: str = Field(default="", description="Base URL for GitHub Pages delivery")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # ==========================================================================
    # Storage Paths
    # ==========================================================================
    archive_path: Path = Field(default=Path("archive"))
    runs_path: Path = Field(default=Path("runs"))
    prompts_path: Path = Field(default=Path("prompts"))
    delivery_pages_dir: Path = Field(default=Path("docs/deliveries"))

    # ==========================================================================
    # GitHub Publish (optional)
    # ==========================================================================
    github_token: str = Field(default="", description="GitHub token for pushing deliveries")
    github_repo: str = Field(default="", description="GitHub repo in owner/name form")
    github_branch: str = Field(default="main", description="GitHub branch to push")
    git_user_name: str = Field(default="", description="Git user.name for automated commits")
    git_user_email: str = Field(default="", description="Git user.email for automated commits")

    # ==========================================================================
    # Model Settings
    # ==========================================================================
    gemini_model: str = Field(default="gemini-3-pro-preview")
    gemini_image_model: str = Field(default="gemini-3-pro-image-preview")
    claude_model: str = Field(default="claude-opus-4-5-20251101")

    # ==========================================================================
    # API Behavior
    # ==========================================================================
    max_retries: int = Field(default=3)
    api_timeout: int = Field(default=120)

    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    use_mock_apis: bool = Field(
        default=True, description="Use mock API responses for testing"
    )
    save_raw_responses: bool = Field(
        default=True, description="Save raw API responses for debugging"
    )

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def get_archive_path(self) -> Path:
        """Get absolute archive path."""
        if self.archive_path.is_absolute():
            return self.archive_path
        return self.project_root / self.archive_path

    def get_runs_path(self) -> Path:
        """Get absolute runs path."""
        if self.runs_path.is_absolute():
            return self.runs_path
        return self.project_root / self.runs_path

    def get_prompts_path(self) -> Path:
        """Get absolute prompts path."""
        if self.prompts_path.is_absolute():
            return self.prompts_path
        return self.project_root / self.prompts_path

    def get_delivery_pages_dir(self) -> Path:
        """Get absolute delivery pages path."""
        if self.delivery_pages_dir.is_absolute():
            return self.delivery_pages_dir
        return self.project_root / self.delivery_pages_dir

    def has_gemini_key(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here")

    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(
            self.anthropic_api_key and self.anthropic_api_key != "your_anthropic_api_key_here"
        )

    def has_nanobanana_key(self) -> bool:
        """Check if Nano Banana API key is configured."""
        return bool(
            self.nanobanana_api_key and self.nanobanana_api_key != "your_nanobanana_api_key_here"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
