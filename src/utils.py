import logging
import time
from typing import Dict, Any
from collections import deque
import json

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_message_buffer(maxlen: int = 100) -> deque:
    """Create a message buffer with timestamp"""
    return deque(maxlen=maxlen)

def get_timestamp() -> float:
    """Get current timestamp"""
    return time.time()

def safe_json_loads(data: str) -> Dict[str, Any]:
    """Safely parse JSON data"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return {}

def format_message_for_analysis(messages: list) -> str:
    """Format messages for ChatGPT analysis"""
    if not messages:
        return ""
    
    formatted = []
    for msg in messages:
        if isinstance(msg, dict) and 'data' in msg:
            msg_type = msg.get('type', 'unknown')
            data = msg['data']
            timestamp = msg.get('timestamp', 0)
            
            if msg_type == 'trade':
                # Format trade data
                token = data.get('token', 'Unknown')
                amount = data.get('amount', 'Unknown')
                price = data.get('price', 'Unknown')
                side = data.get('side', 'Unknown')
                formatted.append(f"[{timestamp}] TRADE: {side} {amount} {token} @ {price}")
            
            elif msg_type == 'new_token':
                # Format new token data
                token = data.get('token', 'Unknown')
                name = data.get('name', 'Unknown')
                formatted.append(f"[{timestamp}] NEW TOKEN: {name} ({token})")
            
            elif msg_type == 'general':
                # Format general data
                formatted.append(f"[{timestamp}] DATA: {str(data)}")
            
            else:
                # Fallback for other message types
                formatted.append(f"[{timestamp}] {msg_type.upper()}: {str(data)}")
        else:
            formatted.append(str(msg))
    
    return "\n".join(formatted)

def validate_token_address(address: str) -> bool:
    """Validate Solana token address format"""
    if not address or not isinstance(address, str):
        return False
    # Basic Solana address validation (44 characters, base58)
    return len(address) == 44 and address.isalnum()
