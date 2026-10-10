def search_pattern(value: str) -> str:
    """Treat %, _ and backslash as literal search text, not LIKE operators."""
    return "%" + value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
