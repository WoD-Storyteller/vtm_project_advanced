from enum import Enum

class AttackOutcome(str, Enum):
    FAIL = "fail"
    SUCCESS = "success"
    BESTIAL_SUCCESS = "bestial_success"
    BESTIAL_FAILURE = "bestial_failure"
    MESSY_CRITICAL = "messy_critical"