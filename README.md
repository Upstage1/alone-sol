# 🤖 Pump.fun ChatGPT Bot

A real-time bot that analyzes pump.fun chat messages using ChatGPT-4o mini and provides a web dashboard for monitoring sentiment and activity.

## ✨ Features

- **Real-time Chat Analysis**: Connects to pump.fun chat via WebSocket/Socket.IO
- **AI-Powered Insights**: Uses ChatGPT-4o mini to analyze chat sentiment and themes
- **Web Dashboard**: Beautiful, responsive dashboard for monitoring
- **REST API**: Full API for integration with other tools
- **Automatic Reconnection**: Robust error handling and reconnection logic
- **Statistics Tracking**: Detailed metrics and performance monitoring

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your configuration
# You need to set:
# - OPENAI_API_KEY (required)
# - PUMP_TOKEN_ADDRESS (required)
```

### 3. Configure Your Settings

Edit `.env` file:

```env
# OpenAI API (required)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Pump.Fun settings (required)
PUMP_TOKEN_ADDRESS=9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM

# Optional settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
ANALYSIS_INTERVAL=5
MESSAGE_BUFFER_SIZE=100
```

### 4. Run the Bot

```bash
python main.py
```

### 5. Access the Dashboard

Open your browser and go to: `http://localhost:5000`

## 📊 Dashboard Features

- **Real-time Status**: Bot and connection status indicators
- **Live Messages**: Recent chat messages from pump.fun
- **AI Analysis**: ChatGPT analysis results with sentiment tracking
- **Statistics**: Performance metrics and uptime tracking
- **Auto-refresh**: Updates every 5 seconds automatically

## 🔌 API Endpoints

### Status
```bash
curl http://localhost:5000/api/status
```

### Recent Messages
```bash
curl http://localhost:5000/api/messages?limit=10
```

### Analysis Results
```bash
curl http://localhost:5000/api/analysis?limit=5
```

### Statistics
```bash
curl http://localhost:5000/api/statistics
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  pump.fun Chat      │───▶│  Python Bot Core    │───▶│  OpenAI GPT-4o mini │
│  WebSocket/SocketIO │    │                     │    │  API                │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐    ┌─────────────────────┐
                           │  Flask REST API     │───▶│  Web Dashboard      │
                           │  (localhost:5000)   │    │  (HTML/CSS/JS)      │
                           └─────────────────────┘    └─────────────────────┘
```

## 📁 Project Structure

```
pump_fun_chatgpt_bot/
├── src/
│   ├── __init__.py
│   ├── bot_core.py           # Main bot logic
│   ├── pump_connector.py     # Pump.fun connection
│   ├── chatgpt_client.py     # OpenAI API client
│   ├── api_server.py         # Flask REST API
│   └── utils.py              # Utilities and configuration
├── static/                   # Web assets (if needed)
├── requirements.txt          # Dependencies
├── env.example              # Environment variables template
├── config.py                # Application configuration
├── main.py                  # Entry point
└── README.md               # This file
```

## ⚙️ Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `PUMP_TOKEN_ADDRESS` | - | Pump.fun token address (required) |
| `FLASK_HOST` | `0.0.0.0` | Flask server host |
| `FLASK_PORT` | `5000` | Flask server port |
| `ANALYSIS_INTERVAL` | `5` | Analysis interval in seconds |
| `MESSAGE_BUFFER_SIZE` | `100` | Max messages to keep in memory |
| `MAX_ANALYSIS_RESULTS` | `50` | Max analysis results to store |

## 🔧 Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black src/ main.py
```

### Linting

```bash
flake8 src/ main.py
```

## 🐛 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   - Make sure you've created a `.env` file with your OpenAI API key

2. **"Failed to connect to pump.fun"**
   - Check your internet connection
   - Verify the token address is correct
   - The bot will automatically retry connection

3. **"OpenAI API error 429"**
   - You've hit the rate limit
   - The bot will automatically retry with backoff

4. **Dashboard not loading**
   - Check that Flask is running on the correct port
   - Try accessing `http://localhost:5000/api/health`

### Logs

Check the `bot.log` file for detailed error information.

## 📈 Performance

- **Memory Usage**: ~50MB typical
- **CPU Usage**: Low (mostly I/O bound)
- **Network**: Minimal (only API calls and WebSocket)
- **Storage**: In-memory only (no database required)

## 🔒 Security

- API keys are never logged
- Input validation on all endpoints
- Rate limiting on API calls
- No persistent data storage

## 📝 License

This project is for educational and research purposes. Please respect pump.fun's terms of service and OpenAI's usage policies.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

If you encounter any issues:

1. Check the logs in `bot.log`
2. Verify your configuration in `.env`
3. Test the API endpoints manually
4. Check the dashboard for error messages

## 🎯 Future Enhancements

- [ ] Export data to CSV/JSON
- [ ] Email/SMS notifications
- [ ] Custom message filters
- [ ] Sentiment graphs and charts
- [ ] Multiple token support
- [ ] Database persistence
- [ ] Docker containerization
