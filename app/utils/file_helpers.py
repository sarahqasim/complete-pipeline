from pathlib import Path


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def safe_stem(path: Path) -> str:
    """Return filename without extension, safe for use as an ID."""
    return path.stem.replace(" ", "_")
