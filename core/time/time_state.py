from __future__ import annotations

from typing import Dict, Any


DEFAULT_TIME_STATE = {
    "night_index": 1,      # which night of the chronicle
    "hour": 21,            # 21 = 9pm, default starting time
    "sunset_hour": 18,     # 6pm
    "sunrise_hour": 6,     # 6am
}


def get_time_state(guild_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures there is a time_state block in guild_data and returns it.
    """
    if "time_state" not in guild_data:
        guild_data["time_state"] = DEFAULT_TIME_STATE.copy()
    else:
        # ensure required keys exist
        ts = guild_data["time_state"]
        for k, v in DEFAULT_TIME_STATE.items():
            ts.setdefault(k, v)

    return guild_data["time_state"]


def advance_time(guild_data: Dict[str, Any], hours: int) -> Dict[str, Any]:
    """
    Advance in-game time by N hours.

    Returns:
    {
      "time_state": ...,
      "crossed_sunrise": bool,
      "near_sunrise": bool
    }
    """
    ts = get_time_state(guild_data)

    crossed_sunrise = False
    near_sunrise = False

    h = ts["hour"]
    sunrise = ts["sunrise_hour"]

    for _ in range(max(0, hours)):
        h += 1
        if h >= 24:
            h = 0
            ts["night_index"] += 1

        # crossing sunrise
        if h == sunrise:
            crossed_sunrise = True

    ts["hour"] = h

    # define "near sunrise" as within 2 hours before
    if (sunrise - ts["hour"]) % 24 <= 2:
        near_sunrise = True

    return {
        "time_state": ts,
        "crossed_sunrise": crossed_sunrise,
        "near_sunrise": near_sunrise,
    }


def format_time(ts: Dict[str, Any]) -> str:
    """
    Returns a human-readable string like:
      "Night 3, 02:00"
    """
    night = ts.get("night_index", 1)
    hour = ts.get("hour", 21)
    return f"Night {night}, {hour:02d}:00"