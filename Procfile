web: cd backend && gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
worker: cd bot && python telegram_bot.py