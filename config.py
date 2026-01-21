import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # OpenAI
    OPENAI_API_KEY:         str = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL:           str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    # Pump.Fun
    PUMP_TOKEN_ADDRESS:     str = os.getenv('PUMP_TOKEN_ADDRESS')
    PUMP_WEBSOCKET_URL:     str = os.getenv('PUMP_WEBSOCKET_URL', 'wss://frontend-api.pump.fun/socket.io/?EIO=4&transport=websocket')

    # Flask
    FLASK_HOST:             str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT:             int = int(os.getenv('FLASK_PORT', 5000))
    DEBUG:                  bool = os.getenv('DEBUG', 'False').lower() == 'true'

    # Bot
    CREATIVE:               int = int(os.getenv('CREATIVE', 1))
    MAX_RETRIES:            int = int(os.getenv('MAX_RETRIES', 2))
    RATE_LIMIT_DELAY:       int = int(os.getenv('RATE_LIMIT_DELAY', 1))
    ANALYSIS_INTERVAL:      int = int(os.getenv('ANALYSIS_INTERVAL', 5))
    MAX_TOKEN_ANSVERS:      int = int(os.getenv('MAX_TOKEN_ANSVERS', 50))
    MESSAGE_BUFFER_SIZE:    int = int(os.getenv('MESSAGE_BUFFER_SIZE', 100))
    MAX_ANALYSIS_RESULTS:   int = int(os.getenv('MAX_ANALYSIS_RESULTS', 50))

