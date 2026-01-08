"""
Configuration constants for the Refactoring Swarm.
"""

# Agent Configuration
MAX_ITERATIONS = 10
QUALITY_THRESHOLD = 8.0  # Minimum pylint score (0-10)
TEST_TIMEOUT = 30  # seconds per test file

# Path Configuration
SANDBOX_DIR = "sandbox"
LOGS_DIR = "logs"

# LLM Configuration
DEFAULT_MODEL = "gemini-1.5-flash"  # Use 1.5-flash for free tier
MAX_TOKENS = 4000
TEMPERATURE = 0.1  # Low temperature for deterministic fixes

# Safety Configuration
ALLOWED_FILE_EXTENSIONS = {".py"}
BLACKLISTED_IMPORTS = [
    "os.system", "subprocess", "eval", "exec",
    "__import__", "open", "shutil.rmtree"
]

# Logging Configuration
LOG_FILE = "logs/experiment_data.json"
MAX_LOG_SIZE_MB = 10