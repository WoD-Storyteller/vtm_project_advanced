from __future__ import annotations

from typing import Dict, Any

# ---------------------------------------------------------------------------
# FULL PREDATOR TYPE LIST FOR VAMPIRE: THE MASQUERADE (V5)
# Organized as a JSON-like structure you can load directly
# ---------------------------------------------------------------------------

PREDATOR_TYPES: Dict[str, Dict[str, Any]] = {
    "Alleycat": {
        "description": "You hunt by stalking, mugging, or attacking people for their blood.",
        "feeding_style": "Violent ambush or assault feeding.",
        "bonuses": {
            "skills": {
                "Brawl": 1,
                "Intimidation": 1,
            },
            "specialties": ["Intimidation: Stickups or Threats"],
            "discipline_dots": ["Potence or Celerity"],
        },
        "advantages": ["Criminal Contacts (•)", "Streetwise (•)"],
        "drawbacks": ["You regularly commit violent acts to feed, risking Masquerade breaches."],
    },

    "Bagger": {
        "description": "You feed from blood bags, morgues, or medical storage.",
        "feeding_style": "Purchased or stolen medical blood.",
        "bonuses": {
            "skills": {"Larceny": 1},
            "specialties": ["Larceny: Breaking into medical storage"],
            "discipline_dots": ["Obfuscate"],
        },
        "advantages": ["Resources (•) OR Contacts: Medical (•)"],
        "drawbacks": ["Reduced Blood Potency effectiveness, bagged blood is thin (Hunger never drops below 2)."],
    },

    "Blood_Leech": {
        "description": "You hunt other vampires for their vitae.",
        "feeding_style": "Vampire-on-vampire predation.",
        "bonuses": {
            "skills": {"Brawl": 1, "Stealth": 1},
            "discipline_dots": ["Fortitude or Protean or Celerity"],
        },
        "advantages": ["Add 2 Feeding-related dice pools when feeding on Kindred."],
        "drawbacks": [
            "Hunted — other vampires may hunt you in return.",
            "Feeding on mortals is less satisfying (Hunger only reduces by 1).",
        ],
    },

    "Cleaver": {
        "description": "You maintain a mortal family or household and feed secretly from them.",
        "feeding_style": "Domestic feeding from loved ones.",
        "bonuses": {
            "skills": {"Persuasion": 1},
            "discipline_dots": ["Dominate or Auspex"],
        },
        "advantages": ["Retainers (•••) OR Herd (••)"],
        "drawbacks": [
            "You risk emotional attachment and Masquerade exposure.",
            "Stains from harming your loved ones are doubled.",
        ],
    },

    "Consensualist": {
        "description": "You feed only from willing mortals.",
        "feeding_style": "Seduction, negotiation, voluntary donors.",
        "bonuses": {
            "skills": {"Persuasion": 1, "Insight": 1},
            "discipline_dots": ["Auspex or Dominate"],
        },
        "advantages": ["Contacts (•) among subcultures that normalize vampirism."],
        "drawbacks": ["You gain a Stain if you ever feed without full consent."],
    },

    "Farmer": {
        "description": "You avoid feeding on humans and prefer animals.",
        "feeding_style": "Animal blood (thin, weak).",
        "bonuses": {
            "skills": {"Survival": 1},
            "discipline_dots": ["Animalism"],
        },
        "advantages": ["Animal Ken (•)"],
        "drawbacks": [
            "Animal blood is weak — Hunger cannot be reduced below 2.",
            "Feeding takes longer (requires 2 feeding checks).",
        ],
    },

    "Osiris": {
        "description": "You are a cult leader, influencer, musician, or charismatic figure.",
        "feeding_style": "Mass adoration, cults, fans, followers.",
        "bonuses": {
            "skills": {"Performance": 1, "Persuasion": 1},
            "specialties": ["Performance: Your Art", "Persuasion: Followers"],
            "discipline_dots": ["Presence"],
        },
        "advantages": ["Fame (• or ••)", "Haven: Lair or Temple (••)"],
        "drawbacks": [
            "Your cult can become unruly, demanding, or suspicious.",
            "Feeding failure attracts police or media attention."
        ],
    },

    "Sandman": {
        "description": "You feed from sleeping victims by breaking into homes or shelters.",
        "feeding_style": "Stealth-feeding on sleepers.",
        "bonuses": {
            "skills": {"Stealth": 1, "Larceny": 1},
            "discipline_dots": ["Obfuscate"],
        },
        "advantages": ["Add +2 dice to feeding on sleeping victims."],
        "drawbacks": ["Breaking-and-entering risks Masquerade breaches and legal trouble."],
    },

    "Siren": {
        "description": "You seduce, charm, or manipulate mortals before feeding.",
        "feeding_style": "Seduction-driven feeding.",
        "bonuses": {
            "skills": {"Persuasion": 1, "Subterfuge": 1},
            "specialties": ["Persuasion: Seduction"],
            "discipline_dots": ["Presence"],
        },
        "advantages": ["Appearance-based bonuses with certain mortals."],
        "drawbacks": ["You gain a Stain for feeding via deception without remorse."],
    },
    
    "Osiris": {
        "description": "You lead a cult or micro-religion, feeding from worshippers.",
        "feeding_style": "Religious or charismatic dominance.",
        "bonuses": {
            "skills": {"Persuasion": 1, "Occult": 1},
            "discipline_dots": ["Presence or Dominate"],
        },
        "advantages": ["Cult Herd (•••)", "Safe Haven (••)"],
        "drawbacks": [
            "Your cult may demand 'miracles' or escalate dangerously.",
            "Masquerade breaches become more likely as your cult grows."
        ],
    },

    "Scene_Queen": {
        "description": "You hunt among nightlife scenes: clubs, raves, parties.",
        "feeding_style": "High-society nightlife hunter.",
        "bonuses": {
            "skills": {"Etiquette": 1, "Subterfuge": 1},
            "discipline_dots": ["Presence"],
        },
        "advantages": ["Contacts: Nightlife (•)", "Fame (•)"],
        "drawbacks": ["Drug-altered blood is unreliable and inconsistent."],
    },

    "Extortionist": {
        "description": "You force mortals into feeding agreements through bribery or blackmail.",
        "feeding_style": "Coercion and leverage.",
        "bonuses": {
            "skills": {"Intimidation": 1, "Subterfuge": 1},
            "discipline_dots": ["Dominate"],
        },
        "advantages": ["Resources (•)", "Criminal Contacts (•)"],
        "drawbacks": ["Mortals may betray you to authorities or hunters."],
    },

    "Graverobber": {
        "description": "Feeds on corpses, morgues, or newly dead bodies.",
        "feeding_style": "Feeding on cadavers.",
        "bonuses": {
            "skills": {"Medicine": 1, "Stealth": 1},
            "discipline_dots": ["Obfuscate or Oblivion"],
        },
        "advantages": ["Hunted less during feeding (corpse blood provides slow, weak reduction)."],
        "drawbacks": ["Hunger cannot be reduced below 3 unless feeding from living targets."],
    },
}

# ---------------------------------------------------------------------------
# Helper Function
# ---------------------------------------------------------------------------

def get_predator_type(name: str) -> Dict[str, Any]:
    """
    Returns data for a predator type by key.
    Case-insensitive and ignores spacing.
    """
    norm = name.lower().replace(" ", "_")
    return PREDATOR_TYPES.get(norm)