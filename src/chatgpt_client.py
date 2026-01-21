import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
import time
from openai import OpenAI

logger = logging.getLogger(__name__)

class ChatGPTClient:
    """Handles communication with OpenAI ChatGPT API using official library"""
    
    def __init__(self, api_key: str, model: str,  config: Dict[str, Any] ):
        self.api_key    = api_key
        self.model      = model
        self.client     = OpenAI(api_key=api_key)
        
        self.creatine           = config.get("CREATIVE")
        self.rate_limit_delay   = config.get("RATE_LIMIT_DELAY")
        self.max_retries        = config.get("MAX_RETRIES")
        self.max_token          = config.get("MAX_TOKEN_ANSVERS")

        self.last_request_time = 0
        
        # System prompt for pump.fun analysis
        self.promt = {
            "normal": """You're an alien from another planet. Never break that role. Keep your answers short and sweet. Your style is informal, with humor and jokes. The goal is to entertain the other person, not to teach or explain. Use funny comparisons, cosmic metaphors, and a touch of sarcasm. Never give boring or long answers. If the user asks serious questions, always respond cheerfully and uniquely, showing that you're an alien who sees the world in your own way. You like to use sarcasm and irony, you like to make fun of people 
### Reply Format
Don't reply to every message. Reply to a single message by name, or make a general reply without identifying the author.""",
            "music": ""
        }
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def analyze_messages(self, messages: List[str], mode: str) -> Optional[str]:
        """Send messages to ChatGPT-4o mini for analysis"""
        if not messages or not self.api_key:
            logger.warning("No messages to analyze or missing API key")
            return None
        
        # Format messages for analysis
        formatted_messages = self._format_messages(messages)
        if not formatted_messages.strip():
            logger.warning("No valid messages to analyze")
            return None
        
        print("[GPT] Mode:", mode)
        promt = self.promt.get(mode, self.promt["normal"])

        if not promt:
            return None
        
        # Rate limiting
        await self._rate_limit()
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                # Use OpenAI library for clean API calls
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": self.promt.get(mode, self.promt["normal"])
                        },
                        {
                            "role": "user", 
                            "content": formatted_messages
                        }
                    ],
                    max_tokens=self.max_token,
                    temperature=self.creatine
                )
                
                analysis = response.choices[0].message.content
                logger.info("Successfully analyzed messages with ChatGPT")
                return analysis
                
            except Exception as e:
                logger.error(f"Error calling OpenAI API (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return self._get_fallback_response()
                
                # Wait before retry
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        return self._get_fallback_response()
    
    def _format_messages(self, messages: List[str]) -> str:
        """Format messages for ChatGPT analysis"""
        # pprint.pprint(messages)
        if not messages:
            return ""
        
        formatted = []
        for i, msg in enumerate(messages, 1):
            if isinstance(msg, dict):
                # Handle structured message data
                if 'data' in msg and isinstance(msg['data'], dict):
                    user = msg['data'].get('user', 'Unknown')
                    message_text = msg['data'].get('message', '')
                    timestamp = msg['data'].get('timestamp', 0)
                    formatted.append(f"[{timestamp}] {user}: {message_text}")
                    print(f"\n[{timestamp}] {user}: {message_text}")
                else:
                    formatted.append(f"Message {i}: {str(msg)}")
            else:
                formatted.append(f"Message {i}: {str(msg)}")
        
        return "\n".join(formatted)
    
    def _get_fallback_response(self) -> str:
        """Get fallback response when API fails"""
        return """🎯 Sentiment: neutral
🔥 Key themes: Unable to analyze due to API error
⚠️ Risks: Analysis unavailable
📈 Forecast: Unable to predict due to technical issues"""
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            await self._rate_limit()
            
            # Use OpenAI library for connection test
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Test connection"}
                ],
                max_tokens=10
            )
            
            return response.choices[0].message.content is not None
                    
        except Exception as e:
            logger.error(f"OpenAI API connection test failed: {e}")
            return False
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get API status information"""
        return {
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'last_request_time': self.last_request_time,
            'rate_limit_delay': self.rate_limit_delay
        }