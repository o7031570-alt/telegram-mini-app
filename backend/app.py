#!/usr/bin/env python3
"""
Flask API backend for Railway deployment with Telegram integration
"""

import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database.storage import ChannelStorage
    STORAGE_AVAILABLE = True
except Exception as e:
    print(f"❌ Database storage import failed: {e}")
    STORAGE_AVAILABLE = False

# ===== Environment Variables for Railway =====
# Telegram Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I')
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', '@for_you_today')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1003791270028')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '7252765971')
MINI_APP_URL = os.environ.get('MINI_APP_URL', 'https://o7031570-alt.github.io/telegram-mini-app/')

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../static',
            template_folder='../frontend')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize storage
if STORAGE_AVAILABLE:
    try:
        storage = ChannelStorage()
        print("✅ Database storage initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database storage: {e}")
        storage = None
else:
    storage = None

# Create dummy storage if needed
if storage is None:
    class DummyStorage:
        def fetch_posts(self, **kwargs): 
            return []
        def count_posts(self, category=None): 
            return 0
        def get_categories(self): 
            return []
        def save_post(self, post_data): 
            return True
    storage = DummyStorage()

# ===== API Routes =====
@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get posts with pagination"""
    try:
        category = request.args.get('category', None)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        if limit <= 0 or limit > 1000:
            limit = 100
        if offset < 0:
            offset = 0
        
        posts = storage.fetch_posts(category=category, limit=limit, offset=offset)
        total_count = storage.count_posts(category)
        
        response = {
            'success': True,
            'data': posts,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total_count,
                'has_more': (offset + len(posts)) < total_count
            },
            'meta': {
                'category_filter': category,
                'count': len(posts),
                'timestamp': datetime.now().isoformat(),
                'channel': CHANNEL_USERNAME
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        error_response = {
            'success': False,
            'error': f'Server error: {str(e)}'
        }
        return jsonify(error_response), 500

@app.route('/api/posts/<int:message_id>', methods=['GET'])
def get_post_by_id(message_id):
    """Get specific post by message ID"""
    try:
        posts = storage.fetch_posts(limit=1000)
        for post in posts:
            if post.get('message_id') == message_id:
                return jsonify({'success': True, 'data': post})
        
        return jsonify({'success': False, 'error': 'Post not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories with counts"""
    try:
        categories = storage.get_categories()
        result = []
        for category in categories:
            count = storage.count_posts(category)
            result.append({'name': category, 'count': count})
        
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        total_posts = storage.count_posts()
        categories = storage.get_categories()
        
        posts = storage.fetch_posts(limit=1000)
        media_stats = {}
        for post in posts:
            media_type = post.get('media_type', 'text')
            media_stats[media_type] = media_stats.get(media_type, 0) + 1
        
        stats = {
            'total_posts': total_posts,
            'media_types': media_stats,
            'categories': len(categories),
            'channel': CHANNEL_USERNAME,
            'mini_app_url': MINI_APP_URL,
            'collected_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': stats})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/telegram-info', methods=['GET'])
def get_telegram_info():
    """Get Telegram configuration info"""
    info = {
        'channel_username': CHANNEL_USERNAME,
        'channel_id': CHANNEL_ID,
        'mini_app_url': MINI_APP_URL,
        'admin_user_id': ADMIN_USER_ID,
        'bot_available': bool(BOT_TOKEN and BOT_TOKEN != '8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I')
    }
    return jsonify({'success': True, 'data': info})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        db_status = 'connected' if storage and hasattr(storage, 'db') else 'no_db'
        
        response = {
            'status': 'healthy',
            'service': 'telegram-mini-app-backend',
            'timestamp': datetime.now().isoformat(),
            'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'development'),
            'database': db_status,
            'version': '1.0.0'
        }
        return jsonify(response), 200
    except Exception as e:
        response = {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(response), 500

# ===== Frontend Serving =====
@app.route('/')
def serve_frontend():
    """Serve frontend HTML"""
    try:
        # Try multiple possible paths
        possible_paths = [
            '../frontend/index.html',
            'frontend/index.html',
            'index.html'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return send_from_directory(os.path.dirname(path), 'index.html')
        
        # If no frontend found, render basic template
        return render_template('index.html' if os.path.exists('../frontend/index.html') else 'index.html')
    except Exception as e:
        return jsonify({
            'error': 'Frontend not found',
            'message': str(e),
            'api_endpoints': {
                '/api/posts': 'Get posts',
                '/api/categories': 'Get categories',
                '/api/stats': 'Get statistics',
                '/api/health': 'Health check'
            }
        }), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    # Try multiple possible locations
    possible_dirs = ['../static', 'static', '../frontend', 'frontend']
    
    for dir_path in possible_dirs:
        full_path = os.path.join(dir_path, filename)
        if os.path.exists(full_path):
            return send_from_directory(dir_path, filename)
    
    return jsonify({'error': 'File not found'}), 404

@app.errorhandler(404)
def not_found(error):
    response = {
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': {
            'GET /': 'Frontend',
            'GET /api/posts': 'Get all posts',
            'GET /api/posts/<message_id>': 'Get specific post',
            'GET /api/categories': 'Get all categories',
            'GET /api/stats': 'Get statistics',
            'GET /api/telegram-info': 'Get Telegram info',
            'GET /api/health': 'Health check'
        },
        'telegram_info': {
            'channel': CHANNEL_USERNAME,
            'mini_app': MINI_APP_URL
        }
    }
    return jsonify(response), 404

# ===== Application Startup =====
def print_startup_info():
    """Print startup information"""
    print("=" * 60)
    print("🚀 Telegram Mini App Backend - Railway Deployment")
    print("=" * 60)
    print(f"📱 Channel: {CHANNEL_USERNAME} (ID: {CHANNEL_ID})")
    print(f"🤖 Bot Token: {'Configured' if BOT_TOKEN else 'Not configured'}")
    print(f"🌐 Mini App URL: {MINI_APP_URL}")
    print(f"👤 Admin User ID: {ADMIN_USER_ID}")
    print(f"💾 Database: {'PostgreSQL' if 'postgresql' in os.environ.get('DATABASE_URL', '') else 'SQLite'}")
    print(f"📊 Storage Status: {'Connected' if STORAGE_AVAILABLE else 'Dummy'}")
    print("-" * 60)
    print("🌐 Available Endpoints:")
    print(f"   • /                     - Frontend")
    print(f"   • /api/posts           - Get posts")
    print(f"   • /api/categories      - Get categories")
    print(f"   • /api/stats           - Get statistics")
    print(f"   • /api/health          - Health check")
    print(f"   • /api/telegram-info   - Telegram info")
    print("=" * 60)

if __name__ == '__main__':
    # Railway configuration
    port = int(os.environ.get("PORT", 8080))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Run database migration on startup
    try:
        from database.migrate import migrate_postgres
        print("🔄 Running database migration...")
        if migrate_postgres():
            print("✅ Database migration completed")
        else:
            print("⚠️ Database migration skipped or failed")
    except Exception as e:
        print(f"⚠️ Could not run migration: {e}")
    
    print_startup_info()
    
    print(f"🚀 Starting server on {host}:{port} (debug={debug})")
    
    app.run(host=host, port=port, debug=debug)