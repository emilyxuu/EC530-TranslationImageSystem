import os
from dotenv import load_dotenv

# Load variables from .env (if the file exists) into os.environ
# If .env doesn't exist, that's fine — we fall back to the defaults below.
load_dotenv()

# Redis connection settings.
# os.getenv("KEY", "default") returns the value from the environment if set,
# or the default string if not.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Optional: Redis password (needed for Redis Cloud, not for local Redis)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)