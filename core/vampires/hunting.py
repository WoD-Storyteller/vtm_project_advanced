# core/vampires/hunting.py

def perform_hunt(zone: str, hunger: int):
    """
    Minimal viable hunt mechanic.
    """
    if zone == "urban":
        return {"result": "success", "hunger_reduced": 2}
    if zone == "suburbs":
        return {"result": "mixed", "hunger_reduced": 1}
    return {"result": "fail", "hunger_reduced": 0}
