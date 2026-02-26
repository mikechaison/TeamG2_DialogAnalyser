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

CLIENT_AGES = ["18-24", "25-34", "35-44", "45-60", "60+"]
CLIENT_PROFESSIONS = [
    "student", "software engineer", "teacher", "accountant", "freelance artist",
    "retired", "small business owner", "doctor", "gamer",

    "data scientist", "QA tester", "digital marketer", "streamer", "crypto trader",
    "system administrator", "UX/UI designer",

    "photographer", "musician", "journalist", "video editor", "social media influencer",

    "construction worker", "mechanic", "farmer", "truck driver", "chef", "plumber",

    "HR manager", "sales representative", "lawyer", "financial analyst", "CEO", "real estate agent",

    "stay-at-home parent", "fitness coach", "researcher", "barista", "professional athlete"
]
TECH_SAVVINESS = ["low (struggles with basic UI)", "medium (knows basics)", "high (experienced user)", "expert (developer/IT)"]
CLIENT_TONES = ["polite", "anxious/panicked", "frustrated", "passive-aggressive", "rushed", "confused"]
URGENCY_LEVELS = ["low (just asking)", "medium (needs it soon)", "high (blocking work/life)", "critical (losing money/time)"]

# --- GENERATION SETTINGS ---

# Parameters for generate.py
GENERATION_MODEL = "gemini-3-flash-preview"
GENERATION_TEMP = 0.8

# Parameters for analyze.py
ANALYSIS_MODEL = "gemini-3-flash-preview"
ANALYSIS_TEMP = 0.1

THINKING_LEVEL = "low"

# Number of messages per generated chat (approximate)
MAX_CHAT_TURNS = 5

# Number of conversations to generate for the dataset
DATASET_SIZE = 50
