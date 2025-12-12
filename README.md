# AI News Agent - Web Application

Modern web app for searching and analyzing news with AI.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

Then open: http://localhost:8000

## 📖 Features

- **Any Topic**: Search for any news topic
- **Multi-Language**: English, German, Spanish, French
- **AI Analysis**: Azure OpenAI classification
- **Real-Time Updates**: Live job status
- **Export**: JSON, CSV, Excel

## 🔑 API Keys Needed

1. **NewsData.io** - Get free key at: https://newsdata.io/
2. **OpenAI** - Get your API key at: https://platform.openai.com/api-keys

## 📝 API Documentation

Interactive docs at: http://localhost:8000/api/docs

## 🏗️ Architecture

```
OpenNewsAgent/
├── main.py              # FastAPI app
├── config.py            # Settings
├── models.py            # Data models
├── services/
│   ├── news_fetcher.py  # NewsData.io
│   ├── ai_analyzer.py   # Azure OpenAI
│   └── job_manager.py   # Job handling
├── static/
│   └── index.html       # Web UI
└── requirements.txt
```

## 📊 Limitations (Free Tier)

- **NewsData.io**: 10 articles per page, limited requests
- Premium support coming soon

## 🔒 Security

- API keys never stored on server
- Passed in requests only
- Browser localStorage for convenience

## 📄 Old Version

Your previous desktop app is backed up in the `backup/` folder.

