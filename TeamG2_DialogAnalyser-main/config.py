import enum

# --- ENUMS FOR CATEGORIZATION ---

class Intent(str, enum.Enum):
    """Categories of customer requests based on task requirements."""
    PAYMENT_ISSUES = "payment_issues"         # проблеми з оплатою
    TECHNICAL_ERRORS = "technical_errors"     # технічні помилки
    ACCOUNT_ACCESS = "account_access"         # доступ до акаунту
    TARIFF_QUESTIONS = "tariff_questions"     # питання по тарифу
    REFUNDS = "refunds"                       # повернення коштів
    OTHER = "other"                           # інше

class Satisfaction(str, enum.Enum):
    """Client satisfaction levels."""
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    UNSATISFIED = "unsatisfied"

class AgentMistake(str, enum.Enum):
    """List of possible agent mistakes."""
    IGNORED_QUESTION = "ignored_question"
    INCORRECT_INFO = "incorrect_info"
    RUDE_TONE = "rude_tone"
    NO_RESOLUTION = "no_resolution"
    UNNECESSARY_ESCALATION = "unnecessary_escalation"

class CaseScenario(str, enum.Enum):
    """Types of scenarios for dataset generation."""
    SUCCESSFUL = "successful"                 # успішні кейси
    PROBLEMATIC = "problematic"               # проблемні кейси
    CONFLICT = "conflict"                     # конфліктні кейси
    AGENT_MISTAKE = "agent_mistake"           # випадки з помилками агента

# --- GENERATION SETTINGS ---

# Parameters for generate.py
GENERATION_MODEL = "gemini-2.5-flash"
GENERATION_TEMP = 0.8

# Parameters for analyze.py
ANALYSIS_MODEL = "gemini-2.5-flash"
ANALYSIS_TEMP = 0.0

# Number of messages per generated chat (approximate)
MAX_CHAT_TURNS = 5