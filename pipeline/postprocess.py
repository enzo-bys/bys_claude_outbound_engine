"""Post-processing pipeline: banned words, dash removal, variable resolution, validation."""

from __future__ import annotations
import re

from pipeline.models import CampaignConfig
from pipeline.prompts import BYS_BANNED_WORDS
from pipeline.utils import log


TEXT_FIELDS = [
    "email1Subject", "email1Body",
    "email2Subject", "email2Body",
    "email3Subject", "email3Body",
    "linkedinInvite", "linkedinDm",
    "callScript",
]


def replace_banned_words(text: str, campaign_banned: list[str] | None = None) -> str:
    """Replace BYS banned words + campaign-specific banned words."""
    result = text
    for word, replacement in BYS_BANNED_WORDS.items():
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        result = pattern.sub(replacement, result)
    # Campaign-specific banned words (no replacement, just flag)
    if campaign_banned:
        for word in campaign_banned:
            if word.lower() in result.lower():
                log(f"Warning: banned word '{word}' found in content", "warn")
    return result


def remove_dashes(text: str) -> str:
    """Remove em dashes and en dashes, replace with commas."""
    result = text
    result = result.replace(" \u2014 ", ", ")
    result = result.replace(" \u2013 ", ", ")
    result = result.replace("\u2014", ",")
    result = result.replace("\u2013", ",")
    return result


def resolve_variables(text: str, lead_data: dict) -> str:
    """Replace {{variable}} placeholders with actual values."""
    result = text
    result = result.replace("{{firstName}}", lead_data.get("firstName", ""))
    result = result.replace("{{lastName}}", lead_data.get("lastName", ""))
    result = result.replace("{{companyName}}", lead_data.get("companyName", ""))
    return result


def validate_field(text: str, field_name: str) -> None:
    """Validate a text field (log warnings, don't block)."""
    if not text:
        return
    if len(text) > 5000:
        log(f"Field '{field_name}' exceeds 5000 chars ({len(text)})", "warn")
    if "{{" in text:
        log(f"Field '{field_name}' still contains unresolved variables", "warn")


def postprocess_emails(
    emails: list[dict],
    campaign_config: CampaignConfig | None = None,
) -> list[dict]:
    """Run full post-processing pipeline on generated emails."""
    banned = campaign_config.banned_words if campaign_config else []

    for email in emails:
        for field in TEXT_FIELDS:
            text = email.get(field, "")
            if not text:
                continue
            text = replace_banned_words(text, banned)
            text = remove_dashes(text)
            text = resolve_variables(text, email)
            validate_field(text, field)
            email[field] = text

    return emails
