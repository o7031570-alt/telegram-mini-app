#!/usr/bin/env python3
"""
Flask API backend for Termux - serves posts from SQLite database
"""

import json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

import sys
sys.path.append('.')
from database.storage import ChannelStorage

# Initialize Flask app
app = Flask(__name__)
CORS(app)

storage = ChannelStorage()

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
            if post['message_id'] == message_id:
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
        storage.count_posts()  # Test connection
        response = {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat(),
            'service': 'telegram-posts-api'
        }
        return jsonify(response), 200
    except Exception as e:
        response = {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(response), 500

@app.errorhandler(404)
def not_found(error):
    response = {
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': {
            'GET /posts': 'Get all posts',
            'GET /posts/<message_id>': 'Get specific post',
            'GET /categories': 'Get all categories',
            'GET /stats': 'Get database statistics',
            'GET /health': 'Health check'
        }
    }
    return jsonify(response), 404

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5000
    debug = True
    
    print(f"Starting Flask server on http://{host}:{port}")
    print(f"Available endpoints:")
    print(f"  GET http://{host}:{port}/posts")
    print(f"  GET http://{host}:{port}/categories")
    print(f"  GET http://{host}:{port}/stats")
    print(f"  GET http://{host}:{port}/health")
    print(f"Press Ctrl+C to stop")
    
    app.run(host=host, port=port, debug=debug)
