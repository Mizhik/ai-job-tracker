def normalize_email(email: str) -> str:
    """Normalize email address by trimming surrounding whitespace and converting to lowercase."""
    return email.strip().lower()
