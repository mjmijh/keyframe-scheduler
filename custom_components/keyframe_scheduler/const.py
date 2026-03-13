"""Constants for Keyframe Scheduler integration."""

from homeassistant.const import Platform

DOMAIN = "keyframe_scheduler"

PLATFORMS = [Platform.SENSOR]

# Storage
STORE_VERSION = 1
STORE_KEY = f"{DOMAIN}.schedules"

# Services
SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_UPLOAD_FROM_FILE = "upload_from_file"

# Service attributes
ATTR_ENTRY_ID = "entry_id"
ATTR_SCHEDULE = "schedule"
ATTR_FILE_PATH = "file_path"

# Default values
DEFAULT_KELVIN = 4000
DEFAULT_DIM = 50
DEFAULT_STEP_MINUTES = 5
