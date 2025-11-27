from __future__ import annotations

from typing import Dict, Any, List, Optional

from core.vtmv5 import character_model
from core.vtmv5 import merits_flaws
from core.vtmv5 import frenzy as frenzy_mod  # may be used by callers
from core.director.state import DirectorState


class V5DirectorAdapter:
    """
    A V5-aware layer for your Director.

    You feed it events (hunt, frenzy, masquerade breach, touchstone death),
    it updates director_state.json and gives you:
      - scene severity
      - thematic weighting
      - flags for the AI Director prompt
    """

    def __init__(self, state: DirectorState):
        self.state = state

    # -------------------------------------------------
    # Event: hunt result
    # -------------------------------------------------
    def on_hunt(
        self,
        player: Dict[str, Any],
        hunt_result: Dict[str, Any],
        zone: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Called after a hunt.
        hunt_result is expected to come from HuntingEngine.hunt()
        or something with similar shape.
        """
        dice_res = hunt_result.get("dice_result", {})
        feeding = hunt_result.get("feeding_result", {})
        source = feeding.get("source", "human")
        messy = dice_res.get("messy_critical", False)
        bestial = dice_res.get("bestial_failure", False)

        # Base pressure from source
        if source == "human":
            self.state.adjust("masquerade_pressure", 1)
        elif source == "animal":
            self.state.adjust("masquerade_pressure", 0)
        elif source == "bagged":
            self.state.adjust("masquerade_pressure", 0)
        elif source == "vampire":
            self.state.adjust("occult_pressure", 1)
            self.state.adjust("political_pressure", 1)

        # Messy/Bestial -> more tension
        if messy:
            self.state.adjust("violence_pressure", 2)
            self.state.adjust("masquerade_pressure", 2)
        if bestial:
            self.state.adjust("violence_pressure", 1)

        if messy or bestial:
            self.state.adjust_theme("violence", +1)
            self.state.adjust_theme("masquerade", +1)

        self.state.save()
        return self.scene_directives_for_player(player)

    # -------------------------------------------------
    # Event: frenzy test result
    # -------------------------------------------------
    def on_frenzy(
        self,
        player: Dict[str, Any],
        frenzy_result: Dict[str, Any],
        context: str = "frenzy",
    ) -> Dict[str, Any]:
        """
        Called after a frenzy test (success or failure).
        frenzy_result is expected from frenzy.frenzy_test().
        """
        failed = frenzy_result.get("failed", False)
        base = frenzy_result.get("result", {})
        messy = base.get("messy_critical", False)
        bestial = base.get("bestial_failure", False)

        if failed:
            # The Beast rampages
            self.state.adjust("violence_pressure", 2)
            self.state.adjust("masquerade_pressure", 2)
        if messy:
            self.state.adjust("violence_pressure", 1)
        if bestial:
            self.state.adjust("violence_pressure", 1)

        self.state.adjust_theme("occult", +1)
        self.state.adjust_theme("mystery", +1)

        self.state.save()
        return self.scene_directives_for_player(player)

    # -------------------------------------------------
    # Event: explicit masquerade breach
    # -------------------------------------------------
    def on_masquerade_breach(
        self,
        player: Optional[Dict[str, Any]],
        severity: int = 1,
        source: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Called when the ST or system declares a breach.

        severity: 1–5
        """
        self.state.adjust("masquerade_pressure", severity)
        if severity >= 3:
            self.state.adjust("si_pressure", severity - 2)

        self.state.save()
        if player:
            return self.scene_directives_for_player(player)
        return self.global_scene_directives()

    # -------------------------------------------------
    # Event: touchstone loss
    # -------------------------------------------------
    def on_touchstone_loss(
        self,
        player: Dict[str, Any],
        name: str,
        deliberate: bool = True,
    ) -> Dict[str, Any]:
        """
        Called when a Touchstone dies (and you've already updated Humanity).
        """
        self.state.adjust("occult_pressure", 1)
        self.state.adjust_theme("mystery", +1)
        self.state.adjust_theme("masquerade", +1)

        if deliberate:
            self.state.adjust("si_pressure", 1)
            self.state.adjust("political_pressure", 1)

        self.state.save()
        return self.scene_directives_for_player(player)

    # -------------------------------------------------
    # Event: political move
    # -------------------------------------------------
    def on_political_event(
        self,
        severity: int = 1,
        occult: bool = False,
    ) -> Dict[str, Any]:
        self.state.adjust("political_pressure", severity)
        if occult:
            self.state.adjust("occult_pressure", 1)

        self.state.save()
        return self.global_scene_directives()

    # -------------------------------------------------
    # Scene directive helpers
    # -------------------------------------------------
    def scene_directives_for_player(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use V5 state + merits/flaws + humanity + stains
        to provide guidance for the next scene.
        """
        character_model.ensure_character_state(player)

        hum = character_model.get_humanity(player)
        stains = character_model.get_stains(player)
        hunger = character_model.get_hunger(player)
        predator = character_model.get_predator_type_name(player) or "None"
        merit_tags = merits_flaws.merit_tags_for_player(player)
        flaw_tags = merits_flaws.flaw_tags_for_player(player)
        touchstones = character_model.list_touchstones(player)

        dir_summary = self.state.summarize()

        personal_threat = 1
        if hunger >= 3:
            personal_threat += 1
        if stains >= 2:
            personal_threat += 1

        personal_themes: List[str] = []

        if hum <= 5:
            personal_themes.extend(["violence", "occult"])

        if "frenzy_prone" in flaw_tags:
            personal_themes.append("violence")
        if "remorse_penalty" in flaw_tags:
            personal_themes.append("masquerade")
        if "stain_sensitivity" in merit_tags:
            personal_themes.append("mystery")

        alive_touchstones = [t for t in touchstones if t.get("alive", True)]
        dead_touchstones = [t for t in touchstones if not t.get("alive", True)]

        if not alive_touchstones and touchstones:
            personal_themes.extend(["occult", "masquerade"])

        return {
            "city_state": dir_summary,
            "personal": {
                "humanity": hum,
                "stains": stains,
                "hunger": hunger,
                "predator_type": predator,
                "merit_tags": merit_tags,
                "flaw_tags": flaw_tags,
                "touchstones_alive": [t["name"] for t in alive_touchstones],
                "touchstones_dead": [t["name"] for t in dead_touchstones],
                "personal_threat": personal_threat,
                "suggested_personal_themes": personal_themes,
            },
        }

    def global_scene_directives(self) -> Dict[str, Any]:
        """
        Only uses global city state, for scenes not focused on a specific PC.
        """
        return {
            "city_state": self.state.summarize(),
        }