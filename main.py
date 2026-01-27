#!/usr/bin/env python3
"""
Main launcher for Telegram Mini App + Bot Project
Run with: python main.py [bot|backend|both]
"""

import sys
import subprocess
import threading
import time
import os
from pathlib import Path

def run_bot():
    """Run the Telegram bot"""
    print("🤖 Starting Telegram Bot...")
    subprocess.run([sys.executable, "bot/telegram_bot.py"])

def run_backend():
    """Run the Flask backend"""
    print("🌐 Starting Flask Backend...")
    subprocess.run([sys.executable, "backend/app.py"])

def run_both():
    """Run both bot and backend in separate threads"""
    print("🚀 Starting both Telegram Bot and Flask Backend...")
    print("📱 Mini App URL: http://localhost:5000")
    print("📁 Frontend: file://" + str(Path("frontend/index.html").absolute()))
    print("==================================================")
    
    # Create threads
    bot_thread = threading.Thread(target=run_bot)
    backend_thread = threading.Thread(target=run_backend)
    
    # Start threads
    bot_thread.daemon = True
    backend_thread.daemon = True
    
    bot_thread.start()
    backend_thread.start()
    
    print("✅ Both services are running!")
    print("🤖 Bot: Monitoring Telegram channel")
    print("🌐 Backend: Serving API on http://localhost:5000")
    print("📱 Mini App: Open in browser: file://" + str(Path("frontend/index.html").absolute()))
    print("==================================================")
    print("📋 Available API endpoints:")
    print("   • http://localhost:5000/posts")
    print("   • http://localhost:5000/categories")
    print("   • http://localhost:5000/stats")
    print("   • http://localhost:5000/health")
    print("==================================================")
    print("🛑 Press Ctrl+C to stop all services")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        sys.exit(0)

def show_help():
    """Show help message"""
    print("Telegram Mini App + Bot Project Launcher")
    print("Usage: python main.py [option]")
    print("\nOptions:")
    print("  bot       - Run Telegram bot only")
    print("  backend   - Run Flask backend only")
    print("  both      - Run both bot and backend (default)")
    print("  help      - Show this help message")
    print("\nExamples:")
    print("  python main.py bot")
    print("  python main.py backend")
    print("  python main.py both")

if __name__ == "__main__":
    # Check for command line argument
    if len(sys.argv) > 1:
        option = sys.argv[1].lower()
        
        if option == "bot":
            run_bot()
        elif option == "backend":
            run_backend()
        elif option == "both":
            run_both()
        elif option in ["help", "-h", "--help"]:
            show_help()
        else:
            print(f"❌ Unknown option: {option}")
            show_help()
    else:
        # Default: run both
        run_both()
