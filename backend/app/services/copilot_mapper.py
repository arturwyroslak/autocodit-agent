from enum import Enum

# CopilotAction must be a Pydantic-compatible type (preferably an Enum)
class CopilotAction(str, Enum):
    PLAN = "plan"
    APPLY = "apply"
    TEST = "test"
    REVIEW = "review"
    FIX = "fix"
    REFACTOR = "refactor"
    DOCUMENT = "document"
    OPTIMIZE = "optimize"

def mapCopilotToTask(action_str: str):
    # Example mapping
    mapping = {
        "plan": CopilotAction.PLAN,
        "apply": CopilotAction.APPLY,
        "test": CopilotAction.TEST,
        "review": CopilotAction.REVIEW,
        "fix": CopilotAction.FIX,
        "refactor": CopilotAction.REFACTOR,
        "document": CopilotAction.DOCUMENT,
        "optimize": CopilotAction.OPTIMIZE,
    }
    return mapping.get(action_str, CopilotAction.PLAN)
