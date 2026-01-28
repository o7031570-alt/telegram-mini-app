#!/usr/bin/env python3
"""
Flask API for Telegram Mini App - Railway Deployment
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --- Python Path Fix ---
# backend folder ထဲကနေ အပြင်က database folder ကို မြင်နိုင်အောင် path ထည့်ပေးခြင်း
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Environment variables ရယူခြင်း
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I')
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', '@for_you_today')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1003791270028')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '7252765971')
MINI_APP_URL = os.environ.get('MINI_APP_URL', 'https://o7031570-alt.github.io/telegram-mini-app/')

# Flask app အား စတင်ခြင်း
app = Flask(__name__)
CORS(app)

STORAGE_AVAILABLE = False
storage = None

# Database storage အား import လုပ်ရန် ကြိုးစားခြင်း
try:
    from database.storage import ChannelStorage
    storage = ChannelStorage()
    STORAGE_AVAILABLE = True
    print("✅ Database storage imported successfully from root folder")
except ImportError as e:
    print(f"⚠️ Could not import storage module: {e}")
except Exception as e:
    print(f"❌ Database error: {e}")

# Routes
@app.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'Telegram Mini App API is running',
        'channel': CHANNEL_USERNAME,
        'database_status': 'Connected' if STORAGE_AVAILABLE else 'Dummy Mode'
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'storage': STORAGE_AVAILABLE
    })

@app.route('/api/posts')
def get_posts():
    if not STORAGE_AVAILABLE:
        # Database မရှိပါက dummy data ပြပေးခြင်း
        return jsonify([
            {
                'id': 1,
                'text': 'Sample post (Database not connected)',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'category': 'General'
            }
        ])
    
    try:
        posts = storage.get_all_posts()
        return jsonify(posts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)