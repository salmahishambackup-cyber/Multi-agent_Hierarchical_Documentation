def generate_id(prefix: str, index: int) -> str:
    """
    Generate a stable, human-readable ID.
    Example: CLAIM_0001
    """
    return f"{prefix.upper()}_{index:04d}"