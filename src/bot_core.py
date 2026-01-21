import asyncio
import logging
from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime
import time

# from .pump_connector import PumpFunConnector
from .pump_chat_client import PumpChatClient
from .chatgpt_client import ChatGPTClient
from .utils import format_message_for_analysis, get_timestamp

# import pprint

logger = logging.getLogger(__name__)

class BotCore:
    """Main bot logic that coordinates pump.fun connection and ChatGPT analysis"""
    
    def __init__(self, openai_key: str, token_address: str, config: Dict[str, Any]):
        # self.pump_connector = PumpFunConnector(
        #     buffer_size=config.get('MESSAGE_BUFFER_SIZE', 100)
        # )
        self.pumpChatClient = PumpChatClient(
            room_id=token_address,
            buffer_size=config.get('MESSAGE_BUFFER_SIZE')
        )

        self.chatgpt_client = ChatGPTClient(
            api_key=openai_key,
            model=config.get('OPENAI_MODEL'),
            config=config
        )
        
        self.token_address = token_address
        self.analysis_interval = config.get('ANALYSIS_INTERVAL', 5)
        self.max_analysis_results = config.get('MAX_ANALYSIS_RESULTS', 50)
        
        # Data storage
        self.analysis_results = deque(maxlen=self.max_analysis_results)
        self.is_running = False
        self.is_paused = False
        self.mode = "normal"
        self.start_time = None
        self.last_analysis_time = 0
        self.last_ai_call_time = 0.0
        self.last_processed_message_id = 0
        self.total_messages_processed = 0
        self.total_analyses_performed = 0
        self.last_error = None

        self.id = 0
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'analyses_performed': 0,
            'api_errors': 0,
            'connection_errors': 0,
            'last_analysis': None,
            'uptime': 0
        }
    
    async def start(self) -> bool:
        """Start the bot"""
        try:
            logger.info(f"Starting bot for token: {self.token_address}")
            self.start_time = get_timestamp()
            self.is_running = True
            
            # Test OpenAI connection
            if not await self.chatgpt_client.test_connection():
                logger.error("OpenAI API connection test failed")
                return False
            
            # Connect to pump.fun
            # if not await self.pump_connector.connect_to_chat(self.token_address):
            #     logger.error("Failed to connect to pump.fun")
            #     return False
            
            if not self.pumpChatClient.connect():
                logger.error("Failed to connect to pump.fun")
                return False
            
            # Start the main processing loop
            await self._run_main_loop()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            self.last_error = str(e)
            return False
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping bot...")
        self.is_running = False
        
        try:
            # await self.pump_connector.disconnect()
            self.pumpChatClient.stop()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def pause(self):
        """Pause the bot"""
        logger.info("Pausing bot...")
        self.is_paused = True
        self.pumpChatClient.set_paused(True)
    
    def resume(self):
        """Resume the bot"""
        logger.info("Resuming bot...")
        self.is_paused = False
        self.pumpChatClient.set_paused(False)
    
    async def _run_main_loop(self):
        """Main processing loop"""
        logger.info("Starting main processing loop")
        
        # Start message listening in background
        # listen_task = asyncio.create_task(self.pump_connector.listen_messages())
        # listen_task = asyncio.create_task(self.pumpChatClient.listen_messages())
        
        try:
            while self.is_running:
                if not self.is_paused and self.mode != "music":
                    await self.process_cycle()
                await asyncio.sleep(self.analysis_interval)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.last_error = str(e)
        finally:
            # Cancel the listening task
            pass
            # listen_task.cancel()
            # try:
            #     await listen_task
            # except asyncio.CancelledError:
            #     pass
    
    async def process_cycle(self):
        """Process one analysis cycle"""
        try:
            # Respect throttle between AI calls (1–2 seconds)
            now_ts = time.time()
            if (now_ts - self.last_ai_call_time) < self.analysis_interval:
                return

            # Fetch only new, unprocessed messages from chat, up to 6 at a time
            batch_limit = min(6, self.analysis_interval if isinstance(self.analysis_interval, int) else 6)
            new_messages, max_id = self.pumpChatClient.get_new_messages(self.last_processed_message_id, batch_limit)

            if not new_messages:
                logger.debug("No new messages to analyze")
                return
            
            # Update statistics
            self.stats['messages_received'] += len(new_messages)
            self.total_messages_processed += len(new_messages)

            # Advance last processed id
            self.last_processed_message_id = max(self.last_processed_message_id, max_id)

            max_lines = max(1, min(self.analysis_interval if isinstance(self.analysis_interval, int) else 6, self.stats.get('messages_received', 0)))
            max_lines = min(max_lines, len(new_messages), self.pumpChatClient.message_history_limit)
            # Also cap by configured buffer size
            max_lines = min(max_lines, self.analysis_interval if isinstance(self.analysis_interval, int) else 6)

            # Format lines as "nickname + message"
            to_analyze = []
            for m in new_messages[:max_lines]:
                username = m.get('username') or m.get('user') or 'Unknown'
                text = m.get('message') or ''
                to_analyze.append(f"{username} + {text}")

            logger.info(f"Processing {len(to_analyze)} new messages for analysis")
            
            # Format messages for analysis
            # formatted_messages = format_message_for_analysis(recent_messages)
            # formatted_messages = format_message_for_analysis(recent_messages)
            
            # if not formatted_messages.strip():
            #     logger.warning("No valid messages to analyze after formatting")
            #     return
            
            # Send to ChatGPT for analysis
            analysis_result = await self.chatgpt_client.analyze_messages(to_analyze, self.mode)
            
            if analysis_result:
                # Store analysis result
                analysis_data = {
                    'id': self.id,
                    'timestamp': get_timestamp(),
                    'datetime': datetime.now().isoformat(),
                    'message_count': len(to_analyze),
                    'analysis': analysis_result,
                    'token_address': self.token_address
                }
                if self.id > 10000:
                    self.id = 0
                else:
                    self.id += 1
                
                self.analysis_results.append(analysis_data)
                self.stats['analyses_performed'] += 1
                self.total_analyses_performed += 1
                self.stats['last_analysis'] = analysis_data['datetime']
                self.last_analysis_time = get_timestamp()
                self.last_ai_call_time = now_ts
                
                logger.info("Analysis completed successfully")
                logger.debug(f"Analysis result: {analysis_result[:100]}...")
            else:
                logger.warning("Failed to get analysis from ChatGPT")
                self.stats['api_errors'] += 1
                
        except Exception as e:
            logger.error(f"Error in process cycle: {e}")
            self.last_error = str(e)
            self.stats['api_errors'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get bot status information"""
        current_time = get_timestamp()
        uptime = current_time - self.start_time if self.start_time else 0
        
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'token_address': self.token_address,
            'uptime_seconds': uptime,
            'start_time': self.start_time,
            'last_analysis_time': self.last_analysis_time,
            'last_error': self.last_error,
            # 'pump_connection': self.pump_connector.get_connection_status(),
            'pump_connection': self.pumpChatClient.get_connection_status(),
            
            'chatgpt_status': self.chatgpt_client.get_api_status(),
            'statistics': {
                **self.stats,
                'uptime': uptime,
                'total_messages_processed': self.total_messages_processed,
                'total_analyses_performed': self.total_analyses_performed
            }
        }
    
    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from pump.fun"""
        # all_messages = self.pump_connector.get_all_messages()

        # return all_messages[-limit:] if all_messages else []
        return self.pumpChatClient.get_count_messages(limit)
    
    def get_analysis_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results"""
        all_results = list(self.analysis_results)
        return all_results[-limit:] if all_results else []
    
    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis result"""
        if self.analysis_results:
            return self.analysis_results[-1]
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics"""
        current_time = get_timestamp()
        uptime = current_time - self.start_time if self.start_time else 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': self._format_uptime(uptime),
            'messages_per_minute': self._calculate_rate(self.total_messages_processed, uptime),
            'analyses_per_minute': self._calculate_rate(self.total_analyses_performed, uptime),
            'success_rate': self._calculate_success_rate(),
            'last_analysis': self.stats.get('last_analysis'),
            'total_messages': self.total_messages_processed,
            'total_analyses': self.total_analyses_performed,
            'api_errors': self.stats['api_errors'],
            'connection_errors': self.stats['connection_errors']
        }
    
    def _change_mode(self, mode: str):
        if mode == "normal":
            self.mode = "normal"
            self.pumpChatClient.set_paused(False)

        elif mode == "music":
            self.mode = "music"
            self.pumpChatClient.set_paused(True)

        else:
            self.mode = "normal"
            self.pumpChatClient.set_paused(False)

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _calculate_rate(self, count: int, uptime: float) -> float:
        """Calculate rate per minute"""
        if uptime <= 0:
            return 0.0
        return (count / uptime) * 60
    
    def _calculate_success_rate(self) -> float:
        """Calculate analysis success rate"""
        total_attempts = self.stats['analyses_performed'] + self.stats['api_errors']
        if total_attempts <= 0:
            return 100.0
        return (self.stats['analyses_performed'] / total_attempts) * 100
