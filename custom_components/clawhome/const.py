"""Constants for the ClawHome integration."""

DOMAIN = "clawhome"
DEFAULT_PORT = 3000
DEFAULT_SCAN_INTERVAL = 30  # seconds

# API endpoints (relative to base URL)
API_INFO = "/api/clawhome/info"
API_BRAIN_STATUS = "/api/brain/status"
API_BRAIN_CONFIG = "/api/brain/config"
API_BRAIN_DAILY_REVIEW = "/api/brain/daily-review"
API_ROOMS = "/api/rooms"
API_RULES = "/api/rules"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

PLATFORMS = ["sensor", "switch", "button", "number"]
