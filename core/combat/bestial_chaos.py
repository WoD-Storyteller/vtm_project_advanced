import random

BESTIAL_CHAOS_TABLE = [
    "You snarl loudly, frightening bystanders. Masquerade risk increases.",
    "You overextend, knocking over furniture or objects nearby.",
    "You shove the target far harder than intended, changing positioning.",
    "You leave claw marks or dents on the environment.",
    "You roar or hiss involuntarily — supernatural menace leaks out.",
    "Your Beast drives a short frenzy-thought: attack the nearest threat.",
    "You cause collateral damage, cracking concrete or breaking glass.",
    "You grab and fling debris accidentally.",
    "Your predatory aura flares — nearby mortals panic.",
    "You lose subtle control, drawing blood unnecessarily."
]


def roll_bestial_chaos() -> str:
    return random.choice(BESTIAL_CHAOS_TABLE)