"""
Configuration management for ReviewMind.
Handles environment variables, default settings, and credential validation.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Search for .env in current working directory and project root
load_dotenv()
current_dir = Path(__file__).resolve().parent.parent
env_path = current_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


@dataclass
class Settings:
    """Application settings and API configurations."""

    # Groq configuration
    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "").strip()
    )
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    )

    # Hindsight configuration
    hindsight_api_key: str = field(
        default_factory=lambda: os.getenv("HINDSIGHT_API_KEY", "").strip()
    )
    hindsight_api_url: str = field(
        default_factory=lambda: os.getenv(
            "HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io"
        ).strip().rstrip("/")
    )
    hindsight_bank_id: str = field(
        default_factory=lambda: os.getenv("HINDSIGHT_BANK_ID", "reviewmind-team").strip()
    )

    # Reviewer behavior settings
    max_code_chars: int = 25000
    default_recall_budget: str = "mid"
    auto_retain_lessons: bool = True

    def is_groq_ready(self) -> bool:
        """Check if Groq API key is present."""
        return bool(self.groq_api_key)

    def is_hindsight_ready(self) -> bool:
        """Check if Hindsight API key and bank ID are present."""
        return bool(self.hindsight_api_key and self.hindsight_bank_id)

    def validate(self) -> dict[str, bool]:
        """Validate presence of key configuration items."""
        return {
            "groq_api_key": self.is_groq_ready(),
            "hindsight_api_key": bool(self.hindsight_api_key),
            "hindsight_bank_id": bool(self.hindsight_bank_id),
            "hindsight_api_url": bool(self.hindsight_api_url),
        }

    def get_missing_credentials_message(self) -> str:
        """Generate human-readable instructions if credentials are missing."""
        missing = []
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY (Required for LLM code review inference)")
        if not self.hindsight_api_key:
            missing.append("HINDSIGHT_API_KEY (Required for persistent team memory)")

        if not missing:
            return "All credentials configured."

        msg = "Missing required environment variables:\n"
        for item in missing:
            msg += f"- {item}\n"
        msg += "\nPlease create a `.env` file in the project root or configure keys in the UI sidebar."
        return msg


# Global default settings instance
settings = Settings()


def get_settings() -> Settings:
    """Retrieve the current settings instance."""
    return settings


def update_settings(
    groq_api_key: Optional[str] = None,
    hindsight_api_key: Optional[str] = None,
    hindsight_bank_id: Optional[str] = None,
    hindsight_api_url: Optional[str] = None,
    groq_model: Optional[str] = None,
) -> Settings:
    """Update settings in-memory (useful for UI overrides)."""
    global settings
    if groq_api_key is not None:
        settings.groq_api_key = groq_api_key.strip()
    if hindsight_api_key is not None:
        settings.hindsight_api_key = hindsight_api_key.strip()
    if hindsight_bank_id is not None:
        settings.hindsight_bank_id = hindsight_bank_id.strip()
    if hindsight_api_url is not None:
        settings.hindsight_api_url = hindsight_api_url.strip().rstrip("/")
    if groq_model is not None:
        settings.groq_model = groq_model.strip()
    return settings
