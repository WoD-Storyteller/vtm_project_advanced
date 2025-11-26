# core/director/director_system/prophecy.py

def resolve_prophecy(state) -> str:
    """
    Pick the highest theme and generate the prophecy hint.
    """
    themes = state.get("themes", {})
    if not themes:
        return "The future is unclear."

    dominant = max(themes, key=themes.get)
    return f"The air hums with {dominant} energy."
