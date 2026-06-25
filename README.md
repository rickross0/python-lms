# 📚 Python Learning Management System

A full-featured Learning Management System with progress tracking, achievements, quizzes, and certificates.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rickross0/python-lms)

## Features

- 📖 **5 Chapters** of Python programming content
- 📝 **Multiple quiz versions** per chapter (A, B, C)
- 🏆 **13 Achievements** to unlock
- 📊 **Progress Dashboard** with visual stats
- 🎓 **Certificate Generator** upon completion
- 🔐 **User registration & login** with persistent progress

## Tech Stack

- Python 3.11+
- Flask
- Gunicorn
- JSON file storage (no database needed)

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`

## Deploy on Render

Click the **Deploy to Render** button above, or follow these steps:

1. Go to [render.com](https://render.com) and create an account
2. Click **New +** → **Web Service**
3. Connect your GitHub repo: `rickross0/python-lms`
4. Select the **Python** runtime
5. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Click **Create Web Service**
