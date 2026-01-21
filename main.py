#!/usr/bin/env python3
"""
Pump.fun ChatGPT Bot - Main Entry Point

A real-time bot that analyzes pump.fun chat messages using ChatGPT-4o mini
and provides a web dashboard for monitoring.
"""

import asyncio
import os
import sys
import signal
import threading
import logging
from typing import Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from src.bot_core import BotCore
from src.api_server import APIServer
from src.utils import setup_logging

# Global variables for graceful shutdown
bot_instance: Optional[BotCore] = None
api_server: Optional[APIServer] = None
flask_thread: Optional[threading.Thread] = None
loop = None

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    global bot_instance
    if bot_instance:
        print("Stopping bot instance...")
        asyncio.run_coroutine_threadsafe(bot_instance.stop(), loop)
    if flask_thread and flask_thread.is_alive():
        print("Waiting for Flask thread to finish...")
        # Flask обычно завершается при закрытии основного процесса
        # Можно добавить флаг остановки серверу, если он поддерживает
    # Здесь можно добавить завершение других ресурсов
    # Теперь завершаем цикл asyncio
    loop.call_soon_threadsafe(loop.stop)
    sys.exit(0)

def run_flask_server(config: Config, bot_core_instance):
    """Run Flask server in a separate thread"""
    global api_server
    
    try:
        api_server = APIServer(bot_core=bot_core_instance)
        print(f"🌐 Starting Flask server on {config.FLASK_HOST}:{config.FLASK_PORT}")
        print(f"📱 Dashboard: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
        api_server.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")

async def main():
    """Main entry point"""
    global bot_instance, flask_thread, loop
    loop = asyncio.get_running_loop()
    
    # Setup logging
    logger = setup_logging()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = Config()
        
        # Validate required environment variables
        if not config.OPENAI_API_KEY:
            print("❌ Error: Please set OPENAI_API_KEY environment variable")
            print("💡 Copy env.example to .env and fill in your API key")
            sys.exit(1)
        
        if not config.PUMP_TOKEN_ADDRESS:
            print("❌ Error: Please set PUMP_TOKEN_ADDRESS environment variable")
            print("💡 Copy env.example to .env and set the token address")
            sys.exit(1)
        
        print("🔧 Configuration loaded successfully")
        
        # Create bot instance first
        print("🤖 Creating bot instance...")
        bot_instance = BotCore(
            openai_key=config.OPENAI_API_KEY,
            token_address=config.PUMP_TOKEN_ADDRESS,
            config={
                'CREATIVE':                 config.CREATIVE,
                'MAX_RETRIES':              config.MAX_RETRIES,
                'RATE_LIMIT_DELAY':         config.RATE_LIMIT_DELAY,
                'ANALYSIS_INTERVAL':        config.ANALYSIS_INTERVAL,
                'MAX_TOKEN_ANSVERS':        config.MAX_TOKEN_ANSVERS,
                'MESSAGE_BUFFER_SIZE':      config.MESSAGE_BUFFER_SIZE,
                'MAX_ANALYSIS_RESULTS':     config.MAX_ANALYSIS_RESULTS,
                'OPENAI_MODEL':             config.OPENAI_MODEL
            }
        )
        
        # Start Flask server in background thread with bot instance
        flask_thread = threading.Thread(
            target=run_flask_server,
            args=(config, bot_instance),
            daemon=True
        )
        flask_thread.start()
        
        # Give Flask a moment to start
        import time
        time.sleep(2)
        
        # Start the bot (blocking)
        print("🤖 Starting bot main loop...")
        try:
            success = await bot_instance.start()
            if not success:
                print("❌ Failed to start bot")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            logger.exception("Error starting bot")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
