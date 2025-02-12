# Cryptocurrency Trading Automation System

An automated cryptocurrency trading system that combines LSTM-based price prediction with natural language processing of market events. The system leverages asynchronous processing to handle market API latency and provides remote monitoring through Telegram integration.

## Key Features

- **Hybrid Prediction Model**: Combines LSTM networks for technical analysis with NLP-based sentiment analysis of market events
- **Asynchronous Architecture**: Built with Python's asyncio for efficient handling of multiple exchange APIs
- **Telegram Integration**: Remote monitoring and control capabilities through a custom Telegram bot interface
- **Multi-Exchange Support**: Compatible with major cryptocurrency exchanges (Binance, Bittrex, Huobi)
- **Real-time Event Processing**: Monitors and analyzes market-moving events like new listings and partnerships
- **Automated Trading**: Executes trades based on combined signals from technical and sentiment analysis

## Technical Implementation

### Core Components

- **LSTM Model**: Processes historical price and volume data to predict short-term price movements
- **Sentiment Analyzer**: Evaluates market news and events using natural language processing
- **Async Market Interface**: Handles exchange API communications with non-blocking operations
- **Telegram Manager**: Provides real-time monitoring and remote command execution

### Architecture

```
├── main.py           # Main entry point and async orchestrator
├── Trader.py         # Trading logic and order execution
├── Market.py         # Exchange API interface layer
├── Predictor.py      # LSTM model implementation
├── learn.py          # Model training functionality
├── preprocessing.py  # Data preprocessing pipeline
└── visualization.py  # Trading performance visualization
```

### Asynchronous Design

The system utilizes Python's asyncio for efficient handling of market operations:

- Parallel processing of multiple exchange APIs
- Non-blocking order execution and monitoring
- Real-time data streaming and analysis
- Concurrent event processing and trade execution

### Telegram Integration

Remote management features include:

- Real-time performance monitoring
- Trade execution notifications
- Remote command execution
- Portfolio status updates
- Market event alerts

## Performance

- 4.1% net profit over 15-month testing period
- Outperformed traditional single-input LSTM models
- Successfully processed multiple market events simultaneously
- Maintained stable operation during high-volatility periods

## Requirements

- Python 3.6+
- TensorFlow 2.0+
- python-telegram-bot
- ccxt (cryptocurrency exchange trading library)
- pandas, numpy, scikit-learn

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure exchange API keys in `settings.py`
4. Set up Telegram bot token and chat ID
5. Run the system: `python main.py`

## Configuration

Create a `settings.py` file with your API credentials:

```python
# Exchange API credentials
binance_APIKEY = "your_binance_api_key"
binance_SECRET = "your_binance_secret"

# Telegram configuration
telegram_token = "your_telegram_bot_token"
telegram_chat_id = "your_chat_id"
```

## Usage

### Starting the System

```bash
python main.py
```

### Telegram Commands

- `/status` - Get current portfolio status
- `/profit` - View profit/loss metrics
- `/trade <symbol> <side> <amount>` - Execute manual trade
- `/stop` - Safely stop the trading system

## License

MIT License - see LICENSE file for details