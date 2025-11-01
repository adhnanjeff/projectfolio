# Configuration file for CAN Bus IDS System

# CAN Bus Configuration
CAN_CHANNEL = "vcan0"
CAN_INTERFACE = "socketcan"

# File Paths
LOG_FILE = "can_log.csv"
MODEL_FILE = "ids_model.pkl"
TRAINING_DATA_FILE = "can_data.csv"

# IDS Configuration
CONTAMINATION_RATE = 0.1
RANDOM_STATE = 42
RECV_TIMEOUT = 2.0

# Enhanced ML Configuration
WINDOW_SIZE_SECONDS = 5.0
FEATURE_EXTRACTION_ENABLED = True
MODEL_TYPES = ['isolation_forest', 'xgboost', 'random_forest']
TIME_SERIES_FEATURES = True

# Dashboard Configuration
REFRESH_INTERVAL = 2  # seconds
MAX_DISPLAY_ROWS = 50
DASHBOARD_TITLE = "🚗 Advanced CAN Bus IDS"

# Attack Types Configuration
ATTACK_TYPES = {
    "DOS": {"name": "Denial of Service", "color": "#FF4B4B", "icon": "💥"},
    "FUZZING": {"name": "Fuzzing Attack", "color": "#FF8C00", "icon": "🎯"},
    "REPLAY": {"name": "Replay Attack", "color": "#9932CC", "icon": "🔄"},
    "SPOOFING": {"name": "Spoofing Attack", "color": "#DC143C", "icon": "🎭"},
    "FLOODING": {"name": "Message Flooding", "color": "#B22222", "icon": "🌊"},
    "NORMAL": {"name": "Normal Traffic", "color": "#32CD32", "icon": "✅"}
}

# CAN Message IDs
CAN_IDS = {
    "SPEED": 0x100,
    "RPM": 0x101,
    "BRAKE": 0x102,
    "STEERING": 0x103,
    "ENGINE_TEMP": 0x104,
    "FUEL_LEVEL": 0x105
}

# Attack Parameters
ATTACK_PARAMS = {
    "DOS": {"burst_count": 100, "interval": 0.01},
    "FUZZING": {"random_ids": True, "random_data": True},
    "REPLAY": {"replay_count": 5, "interval": 0.5},
    "SPOOFING": {"fake_values": True},
    "FLOODING": {"message_rate": 50, "duration": 10}
}