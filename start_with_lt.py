#!/usr/bin/env python3
"""
Start Flask backend + Localtunnel automatically
"""

import subprocess
import time
import threading
import sys
import re
from pathlib import Path
import requests

FLASK_PORT = 5000

def run_flask():
    """Start Flask backend"""
    print(f"🚀 Starting Flask backend on port {FLASK_PORT}...")
    subprocess.run([sys.executable, "backend/app.py"])

def start_localtunnel():
    """Start localtunnel and get public URL"""
    print("🔗 Starting Localtunnel...")
    
    # Start localtunnel in background
    lt_process = subprocess.Popen(
        ["lt", "--port", str(FLASK_PORT), "--subdomain", "telegram-mini-app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for tunnel to establish
    time.sleep(5)
    
    # Try to get URL from stdout
    lt_url = None
    for _ in range(10):  # Try for 10 seconds
        line = lt_process.stdout.readline()
        if line:
            print(f"LT Output: {line.strip()}")
            # Look for URL in output
            url_match = re.search(r'https?://[^\s]+', line)
            if url_match:
                lt_url = url_match.group(0)
                break
        time.sleep(1)
    
    if not lt_url:
        # Default URL pattern
        lt_url = "https://telegram-mini-app.loca.lt"
    
    return lt_url, lt_process

def update_config_with_lt_url(lt_url):
    """Update MINI_APP_URL in config.py"""
    config_file = Path("config.py")
    
    # Create config.py if doesn't exist
    if not config_file.exists():
        print("📝 Creating config.py...")
        with open(config_file, 'w') as f:
            f.write(f'MINI_APP_URL = "{lt_url}"\n')
            f.write('BOT_TOKEN = "8514370308:AAG-qf5sR3IV9Ad0T0RZM9xCXv-59FPyR7I"\n')
            f.write('CHANNEL_USERNAME = "@for_you_today"\n')
            f.write('CHANNEL_ID = -1003791270028\n')
            f.write('ADMIN_USER_ID = 7252765971\n')
            f.write('FLASK_HOST = "127.0.0.1"\n')
            f.write('FLASK_PORT = 5000\n')
        return lt_url
    
    # Read and update existing config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Update MINI_APP_URL
    if 'MINI_APP_URL =' in content:
        # Replace existing URL
        new_content = re.sub(
            r'MINI_APP_URL = "[^"]*"',
            f'MINI_APP_URL = "{lt_url}"',
            content
        )
    else:
        # Add MINI_APP_URL if not exists
        new_content = content + f'\nMINI_APP_URL = "{lt_url}"\n'
    
    with open(config_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated MINI_APP_URL in config.py: {lt_url}")
    return lt_url

def update_frontend_for_lt(lt_url):
    """Update frontend to use localtunnel URL"""
    frontend_file = Path("frontend/index.html")
    if not frontend_file.exists():
        return
    
    with open(frontend_file, 'r') as f:
        content = f.read()
    
    # Update API_BASE_URL for localtunnel
    new_content = re.sub(
        r'const API_BASE_URL = \'[^\']*\';',
        f'const API_BASE_URL = \'{lt_url}\';',
        content
    )
    
    with open(frontend_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated frontend API_BASE_URL: {lt_url}")

def test_lt_connection(lt_url):
    """Test if localtunnel is working"""
    try:
        print(f"🔍 Testing connection to {lt_url}...")
        response = requests.get(f"{lt_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Connection test successful!")
            return True
    except Exception as e:
        print(f"⚠️ Connection test failed: {e}")
    return False

def main():
    print("=" * 60)
    print("🤖 Telegram Mini App + Localtunnel Starter")
    print("=" * 60)
    
    # Check if lt command exists
    try:
        subprocess.run(["lt", "--help"], capture_output=True, check=True)
    except:
        print("❌ Localtunnel not installed!")
        print("   Run: npm install -g localtunnel")
        return
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    time.sleep(3)
    
    # Start Localtunnel
    print("\n🌐 Starting public tunnel with Localtunnel...")
    lt_url, lt_process = start_localtunnel()
    
    print(f"\n✅ Localtunnel Active!")
    print(f"🌍 Public URL: {lt_url}")
    
    # Update configuration
    update_config_with_lt_url(lt_url)
    update_frontend_for_lt(lt_url)
    
    # Test connection
    time.sleep(2)
    test_lt_connection(lt_url)
    
    print("\n" + "=" * 60)
    print("📋 IMPORTANT NEXT STEPS:")
    print("=" * 60)
    print("1. 📱 Update Telegram Bot Menu Button:")
    print(f"   Go to @BotFather → /mybots → your bot →")
    print(f"   Bot Settings → Menu Button → Set URL to:")
    print(f"   {lt_url}")
    print("\n2. 🔄 Restart your Telegram bot:")
    print("   python bot/telegram_bot.py")
    print("\n3. 🌐 Open frontend in browser:")
    print(f"   {lt_url}")
    print("=" * 60)
    print("\n✅ System is running! Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        # Keep running
        lt_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Localtunnel and Flask...")
        lt_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
