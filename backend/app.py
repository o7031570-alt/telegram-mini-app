import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database.storage import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend')

# Configure CORS
cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
if not cors_origins or cors_origins[0] == '':
    cors_origins = ['https://o7031570-alt.github.io', 'http://localhost:5000', 'http://localhost:3000']

CORS(app, origins=cors_origins, supports_credentials=True)

# Initialize database
db_manager = DatabaseManager()

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

@app.route('/')
def index():
    """Redirect to GitHub Pages Mini App"""
    return jsonify({
        'message': 'Welcome to For You Today API',
        'mini_app': 'https://o7031570-alt.github.io/telegram-mini-app/',
        'channel': 'https://t.me/for_you_today',
        'endpoints': {
            'posts': '/api/posts',
            'search': '/api/posts/search',
            'stats': '/api/stats',
            'health': '/health'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        post_count = db_manager.get_post_count()
        return jsonify({
            'status': 'healthy',
            'service': 'For You Today API',
            'channel': '@for_you_today',
            'post_count': post_count,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'development'),
            'database': db_manager.get_database_info()
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """API endpoint to get all posts"""
    try:
        category = request.args.get('category')
        limit = request.args.get('limit', type=int)
        page = request.args.get('page', 1, type=int)
        
        posts = db_manager.get_all_posts(category=category, limit=limit)
        
        return jsonify({
            'success': True,
            'data': posts,
            'count': len(posts),
            'channel': '@for_you_today',
            'mini_app': 'https://o7031570-alt.github.io/telegram-mini-app/'
        })
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'channel': '@for_you_today'
        }), 500

@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """Search posts by content"""
    try:
        query = request.args.get('q', '')
        category = request.args.get('category')
        
        if not query:
            return jsonify({
                'success': True,
                'data': [],
                'count': 0,
                'message': 'Please provide a search query'
            })
        
        posts = db_manager.search_posts(query, category=category)
        
        return jsonify({
            'success': True,
            'data': posts,
            'count': len(posts),
            'query': query,
            'channel': '@for_you_today'
        })
    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get channel statistics"""
    try:
        total_posts = db_manager.get_post_count()
        categories = db_manager.get_category_stats()
        
        return jsonify({
            'success': True,
            'channel': {
                'username': '@for_you_today',
                'id': '-1003791270028',
                'url': 'https://t.me/for_you_today'
            },
            'statistics': {
                'total_posts': total_posts,
                'categories': categories,
                'last_updated': datetime.utcnow().isoformat()
            },
            'mini_app': 'https://o7031570-alt.github.io/telegram-mini-app/'
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/posts/<int:message_id>', methods=['GET'])
def get_post(message_id):
    """Get a specific post by message ID"""
    try:
        post = db_manager.get_post_by_id(message_id)
        if post:
            return jsonify({
                'success': True,
                'data': post,
                'channel': '@for_you_today'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Post not found',
                'message_id': message_id
            }), 404
    except Exception as e:
        logger.error(f"Error getting post {message_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'Check / for available endpoints',
        'channel': '@for_you_today'
    }), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'channel': '@for_you_today'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting For You Today API for @for_you_today")
    logger.info(f"🌐 Listening on {host}:{port}")
    logger.info(f"🔗 Mini App: https://o7031570-alt.github.io/telegram-mini-app/")
    logger.info(f"📢 Channel: https://t.me/for_you_today")
    
    app.run(host=host, port=port, debug=debug)