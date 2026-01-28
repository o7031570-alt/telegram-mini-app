#!/usr/bin/env python3
"""
Flask API for Telegram Mini App - Railway Deployment
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import storage
try:
    from database.storage import storage
    STORAGE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import storage module: {e}")
    STORAGE_AVAILABLE = False
    # Create dummy storage
    class DummyStorage:
        def fetch_posts(self, **kwargs): 
            return [
                {"id": 1, "message_id": 1, "content": "Sample post 1", "media_type": "text", "category": "general"},
                {"id": 2, "message_id": 2, "content": "Sample post 2", "media_type": "text", "category": "news"}
            ]
        def count_posts(self, category=None): 
            return 2
        def get_categories(self): 
            return ["general", "news"]
    storage = DummyStorage()
except Exception as e:
    print(f"⚠️ Storage initialization error: {e}")
    STORAGE_AVAILABLE = False
    class DummyStorage:
        def fetch_posts(self, **kwargs): return []
        def count_posts(self, category=None): return 0
        def get_categories(self): return []
    storage = DummyStorage()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I')
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', '@for_you_today')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1003791270028')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '7252765971')
MINI_APP_URL = os.environ.get('MINI_APP_URL', 'https://o7031570-alt.github.io/telegram-mini-app/')

# ===== API Routes =====
@app.route('/')
def home():
    """Home page with API info"""
    return jsonify({
        'service': 'Telegram Mini App API',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            '/': 'API information',
            '/api/posts': 'Get posts',
            '/api/categories': 'Get categories',
            '/api/stats': 'Get statistics',
            '/api/health': 'Health check',
            '/frontend': 'Frontend interface'
        },
        'telegram': {
            'channel': CHANNEL_USERNAME,
            'mini_app_url': MINI_APP_URL
        }
    })

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get posts with optional filtering"""
    try:
        category = request.args.get('category')
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validate parameters
        limit = min(limit, 1000)  # Max 1000 posts
        limit = max(limit, 1)     # Min 1 post
        offset = max(offset, 0)   # Min offset 0
        
        posts = storage.fetch_posts(limit=limit, offset=offset)
        
        # Filter by category if specified
        if category:
            posts = [p for p in posts if p.get('category') == category]
        
        total = storage.count_posts(category)
        
        return jsonify({
            'success': True,
            'data': posts,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total,
                'has_more': (offset + len(posts)) < total
            },
            'count': len(posts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories with counts"""
    try:
        categories = storage.get_categories()
        result = []
        
        for category in categories:
            count = storage.count_posts(category)
            result.append({
                'name': category,
                'count': count
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        total_posts = storage.count_posts()
        categories = storage.get_categories()
        
        posts = storage.fetch_posts(limit=100)
        media_stats = {}
        
        for post in posts:
            media_type = post.get('media_type', 'text')
            media_stats[media_type] = media_stats.get(media_type, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_posts': total_posts,
                'categories_count': len(categories),
                'media_types': media_stats,
                'categories': categories,
                'collected_at': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if STORAGE_AVAILABLE else 'dummy',
        'environment': 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'
    })

@app.route('/api/telegram-info', methods=['GET'])
def telegram_info():
    """Get Telegram configuration"""
    return jsonify({
        'success': True,
        'data': {
            'channel_username': CHANNEL_USERNAME,
            'channel_id': CHANNEL_ID,
            'admin_user_id': ADMIN_USER_ID,
            'mini_app_url': MINI_APP_URL,
            'bot_token_set': bool(BOT_TOKEN and BOT_TOKEN != 'your_bot_token_here')
        }
    })

# ===== Frontend Serving =====
@app.route('/frontend')
def serve_frontend():
    """Serve frontend HTML"""
    try:
        # Try to find frontend files
        frontend_paths = [
            '../frontend/index.html',
            'frontend/index.html',
            'index.html'
        ]
        
        for path in frontend_paths:
            if os.path.exists(path):
                directory = os.path.dirname(path) if os.path.dirname(path) else '.'
                filename = os.path.basename(path)
                return send_from_directory(directory, filename)
        
        # If no frontend found, show message
        return jsonify({
            'message': 'Frontend not found. Running in API mode.',
            'api_endpoints': ['/api/posts', '/api/categories', '/api/stats', '/api/health']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/frontend/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend"""
    static_dirs = ['../frontend', 'frontend', '.']
    
    for dir_path in static_dirs:
        file_path = os.path.join(dir_path, filename)
        if os.path.exists(file_path):
            return send_from_directory(dir_path, filename)
    
    return jsonify({'error': 'File not found'}), 404

# ===== Error Handlers =====
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': {
            'GET /': 'API information',
            'GET /api/posts': 'Get posts',
            'GET /api/categories': 'Get categories',
            'GET /api/stats': 'Get statistics',
            'GET /api/health': 'Health check',
            'GET /frontend': 'Frontend interface'
        }
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ===== Startup =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0'
    
    print("=" * 60)
    print("🚀 Telegram Mini App Backend")
    print("=" * 60)
    print(f"📡 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📊 Database: {'Connected' if STORAGE_AVAILABLE else 'Dummy/Error'}")
    print(f"📱 Channel: {CHANNEL_USERNAME}")
    print(f"🌐 Frontend: {MINI_APP_URL}")
    print(f"📁 Working directory: {os.getcwd()}")
    print("=" * 60)
    print("Available endpoints:")
    print(f"  http://{host}:{port}/")
    print(f"  http://{host}:{port}/api/health")
    print(f"  http://{host}:{port}/api/posts")
    print(f"  http://{host}:{port}/frontend")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=False)