#!/usr/bin/env python3
"""
Flask API backend for Railway deployment
"""

import json
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import sys
sys.path.append('.')
from database.storage import ChannelStorage

# ===== Environment Variables for Railway =====
# Get environment variables but don't exit if not found
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID')

# Initialize Flask app
app = Flask(__name__)
# Allow all origins for Railway
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize storage
try:
    storage = ChannelStorage()
    print("✅ Database storage initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize database storage: {e}")
    # Create a dummy storage for health check to pass
    class DummyStorage:
        def fetch_posts(self, **kwargs): return []
        def count_posts(self, category=None): return 0
        def get_categories(self): return []
    storage = DummyStorage()

@app.route('/posts', methods=['GET'])
def get_posts():
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
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        error_response = {
            'success': False,
            'error': f'Server error: {str(e)}'
        }
        return jsonify(error_response), 500

@app.route('/posts/<int:message_id>', methods=['GET'])
def get_post_by_id(message_id):
    try:
        posts = storage.fetch_posts(limit=1000)
        for post in posts:
            if post.get('message_id') == message_id:
                return jsonify({'success': True, 'data': post})
        
        return jsonify({'success': False, 'error': 'Post not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = storage.get_categories()
        result = []
        for category in categories:
            count = storage.count_posts(category)
            result.append({'name': category, 'count': count})
        
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        total_posts = storage.count_posts()
        
        posts = storage.fetch_posts(limit=1000)
        media_stats = {}
        for post in posts:
            media_type = post.get('media_type', 'text')
            media_stats[media_type] = media_stats.get(media_type, 0) + 1
        
        stats = {
            'total_posts': total_posts,
            'media_types': media_stats,
            'collected_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': stats})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Simple health check without database dependency
        response = {
            'status': 'healthy',
            'service': 'telegram-posts-api',
            'timestamp': datetime.now().isoformat(),
            'environment': 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'
        }
        return jsonify(response), 200
    except Exception as e:
        response = {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(response), 500

# ===== FRONTEND SERVING FOR RAILWAY =====
@app.route('/')
def serve_frontend():
    """Serve frontend for Railway deployment"""
    try:
        # Try multiple possible paths for frontend files
        possible_paths = [
            os.path.join('frontend', 'index.html'),
            os.path.join('..', 'frontend', 'index.html'),
            'index.html'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return send_from_directory(os.path.dirname(path) if os.path.dirname(path) else '.', 
                                         os.path.basename(path))
        
        # If no frontend found, return API info
        return jsonify({
            'service': 'Telegram Mini App Backend',
            'status': 'running',
            'endpoints': ['/posts', '/categories', '/stats', '/health']
        })
    except Exception as e:
        return jsonify({'error': f'Frontend not found: {str(e)}'}), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files for Railway"""
    # Try multiple possible locations
    possible_dirs = ['frontend', 'static', '.']
    
    for dir_path in possible_dirs:
        file_path = os.path.join(dir_path, filename)
        if os.path.exists(file_path):
            return send_from_directory(dir_path, filename)
    
    return jsonify({'error': 'File not found'}), 404

@app.errorhandler(404)
def not_found(error):
    response = {
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': {
            'GET /': 'API Home / Frontend',
            'GET /posts': 'Get all posts',
            'GET /posts/<message_id>': 'Get specific post',
            'GET /categories': 'Get all categories',
            'GET /stats': 'Get database statistics',
            'GET /health': 'Health check'
        }
    }
    return jsonify(response), 404

# ===== RAILWAY PRODUCTION CONFIGURATION =====
if __name__ == '__main__':
    # Railway uses PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    
    # Railway requires 0.0.0.0 to listen on all interfaces
    host = '0.0.0.0'
    
    # Disable debug mode in production
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Starting Flask server for Railway")
    print(f"🌐 Host: {host}, Port: {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📊 Available endpoints:")
    print(f"   • http://{host}:{port}/")
    print(f"   • http://{host}:{port}/posts")
    print(f"   • http://{host}:{port}/health")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=debug)