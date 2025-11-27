from __future__ import annotations

from typing import Dict, Any, List

# ---------------------------------------------------------------------------
# Full Predator Type list for Vampire: The Masquerade 5th Edition (V5)
# ---------------------------------------------------------------------------

def _norm(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


PREDATOR_TYPES: Dict[str, Dict[str, Any]] = {
    "alleycat": {
        "key": "alleycat",
        "name": "Alleycat",
        "description": "Violent ambush predator hunting via muggings, assaults or direct attacks.",
        "feeding_style": "Violent ambush or assault feeding.",
        "bonuses": {
            "skills": {"Brawl": 1, "Intimidation": 1},
            "specialties": ["Intimidation: Stickups or Threats"],
            "discipline_dots": ["Potence", "Celerity"],
        },
        "advantages": ["Criminal Contacts (•)", "Streetwise (•)"],
        "drawbacks": [
            "You often commit violent crimes when feeding, risking Masquerade and legal trouble."
        ],
    },
    "bagger": {
        "key": "bagger",
        "name": "Bagger",
        "description": "Feeds from stolen or purchased medical blood.",
        "feeding_style": "Purchased or stolen bagged blood from hospitals and clinics.",
        "bonuses": {
            "skills": {"Larceny": 1},
            "specialties": ["Larceny: Medical Theft"],
            "discipline_dots": ["Obfuscate"],
        },
        "advantages": ["Resources (•) or Contacts: Medical (•)"],
        "drawbacks": [
            "Bagged blood is thin: Hunger cannot be reduced below 2 when feeding only from bags."
        ],
    },
    "blood_leech": {
        "key": "blood_leech",
        "name": "Blood Leech",
        "description": "You prey on other vampires for their vitae.",
        "feeding_style": "Feeding primarily on Kindred rather than mortals.",
        "bonuses": {
            "skills": {"Brawl": 1, "Stealth": 1},
            "discipline_dots": ["Fortitude", "Protean", "Celerity"],
        },
        "advantages": [
            "Gain enhanced feeding when drinking from Kindred (can slake more Hunger at once)."
        ],
        "drawbacks": [
            "You are considered a threat by other vampires.",
            "Feeding on mortals feels insufficient: mortal feeding is less effective."
        ],
    },
    "cleaver": {
        "key": "cleaver",
        "name": "Cleaver",
        "description": "Maintains a mortal family or domestic arrangement and feeds from them.",
        "feeding_style": "Domestic feeding on family or household.",
        "bonuses": {
            "skills": {"Persuasion": 1},
            "discipline_dots": ["Dominate", "Auspex"],
        },
        "advantages": ["Retainers (•••) or Herd (••)"],
        "drawbacks": [
            "Harming or endangering your family or household is especially damning (extra Stains at ST discretion)."
        ],
    },
    "consensualist": {
        "key": "consensualist",
        "name": "Consensualist",
        "description": "Feeds only from willing mortals and refuses to violate consent.",
        "feeding_style": "Feeding exclusively from willing donors.",
        "bonuses": {
            "skills": {"Persuasion": 1, "Insight": 1},
            "discipline_dots": ["Auspex", "Dominate"],
        },
        "advantages": ["Contacts (•) among kink, goth, or occult subcultures that accept feeding."],
        "drawbacks": [
            "You gain a Stain whenever you feed without genuine consent (ST final call)."
        ],
    },
    "farmer": {
        "key": "farmer",
        "name": "Farmer",
        "description": "Tries to subsist primarily on animals instead of human blood.",
        "feeding_style": "Feeding on animals in fields, barns, or the wild.",
        "bonuses": {
            "skills": {"Survival": 1},
            "discipline_dots": ["Animalism"],
        },
        "advantages": ["Animal Ken (•) and easier access to animal Herds."],
        "drawbacks": [
            "Animal blood is weak: Hunger cannot be reduced below 2 when feeding only from animals."
        ],
    },
    "osiris": {
        "key": "osiris",
        "name": "Osiris",
        "description": "You are worshipped, adored, or centered in a cult, band, or movement.",
        "feeding_style": "Feeding from cultists, fans, or congregants.",
        "bonuses": {
            "skills": {"Performance": 1, "Persuasion": 1},
            "discipline_dots": ["Presence", "Dominate"],
        },
        "advantages": ["Cult Herd (•••)", "Secure Haven tied to your cult (••)"],
        "drawbacks": [
            "Your cult can spiral out of control, attract hunters, or demand miracles."
        ],
    },
    "sandman": {
        "key": "sandman",
        "name": "Sandman",
        "description": "Feeds from sleeping victims, slipping into homes or hospitals at night.",
        "feeding_style": "Stealthy feeding from the sleeping.",
        "bonuses": {
            "skills": {"Stealth": 1, "Larceny": 1},
            "discipline_dots": ["Obfuscate"],
        },
        "advantages": ["Add bonus dice when feeding from sleeping victims."],
        "drawbacks": [
            "Breaking and entering constantly risks Masquerade breaches and legal trouble."
        ],
    },
    "siren": {
        "key": "siren",
        "name": "Siren",
        "description": "Seduction-based predator who feeds from lovers and admirers.",
        "feeding_style": "Feeding through seduction, romance, and lust.",
        "bonuses": {
            "skills": {"Persuasion": 1, "Subterfuge": 1},
            "discipline_dots": ["Presence"],
        },
        "advantages": ["Often has a ready pool of potential lovers as Herd (• or ••)."],
        "drawbacks": [
            "Frequently manipulates emotions, potentially leading to extra Stains from betrayal or cruelty."
        ],
    },
    "scene_queen": {
        "key": "scene_queen",
        "name": "Scene Queen",
        "description": "Rules a subculture, club scene, or nightlife environment.",
        "feeding_style": "Hunts in clubs, raves, festivals, and nightlife.",
        "bonuses": {
            "skills": {"Etiquette": 1, "Subterfuge": 1},
            "discipline_dots": ["Presence"],
        },
        "advantages": ["Fame (•) and Contacts in nightlife or entertainment scenes."],
        "drawbacks": [
            "Drug- or alcohol-laced blood can cause complications or less effective feeding."
        ],
    },
    "extortionist": {
        "key": "extortionist",
        "name": "Extortionist",
        "description": "Forces mortals into feeding arrangements using blackmail or threats.",
        "feeding_style": "Coercive feeding with leverage, blackmail, or extortion.",
        "bonuses": {
            "skills": {"Intimidation": 1, "Subterfuge": 1},
            "discipline_dots": ["Dominate"],
        },
        "advantages": ["Resources (•) or Criminal Contacts (•) from illicit operations."],
        "drawbacks": [
            "Mortals may betray you to police or hunters when pushed too far."
        ],
    },
    "graverobber": {
        "key": "graverobber",
        "name": "Graverobber",
        "description": "Feeds on corpses, morgues, battlefield dead, or mortuaries.",
        "feeding_style": "Feeds on the recently dead rather than the living.",
        "bonuses": {
            "skills": {"Medicine": 1, "Stealth": 1},
            "discipline_dots": ["Obfuscate", "Oblivion"],
        },
        "advantages": ["Less risk of immediate Masquerade breach while feeding."],
        "drawbacks": [
            "Corpse blood is poor sustenance: Hunger cannot be reduced below 3 on corpses alone."
        ],
    },
}


def list_predator_types() -> list[Dict[str, Any]]:
    """
    Returns a list of predator type dicts sorted by name.
    """
    return sorted(PREDATOR_TYPES.values(), key=lambda p: p["name"])


def get_predator_type(name: str) -> Dict[str, Any] | None:
    """
    Returns predator type dict by name or key (case-insensitive).
    """
    key = _norm(name)
    # direct key
    if key in PREDATOR_TYPES:
        return PREDATOR_TYPES[key]
    # try matching by display name
    for pt in PREDATOR_TYPES.values():
        if _norm(pt["name"]) == key:
            return pt
    return None


def apply_predator_type(player: Dict[str, Any], name: str) -> Dict[str, Any]:
    """
    Sets predator_type and predator_key on a player dict.
    Does NOT automatically change skills or disciplines, since those
    structures vary by implementation. Instead, it returns the predator
    data so the calling code (or Storyteller) can apply changes.

    Returns the predator_type dict or raises ValueError if not found.
    """
    from . import character_model  # local import to avoid circularity

    pt = get_predator_type(name)
    if not pt:
        raise ValueError(f"Unknown predator type: {name}")

    character_model.ensure_character_state(player)
    character_model.set_predator_info(player, pt["key"], pt["name"])

    return pt