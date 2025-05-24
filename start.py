#!/usr/bin/env python3
"""
Startup script for scootdr application
Attempts to find and run the main application file
"""

import os
import sys
import subprocess
import importlib.util

def find_main_file():
    """Find the main application file"""
    # Common entry point patterns
    entry_points = [
        "main.py",
        "app.py", 
        "server.py",
        "run.py",
        "manage.py",
        "wsgi.py"
    ]
    
    for entry in entry_points:
        if os.path.exists(entry):
            return entry
    
    # Look for files with Flask/Django patterns
    for file in os.listdir("."):
        if file.endswith(".py"):
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if any(pattern in content for pattern in [
                        "app.run(",
                        "Flask(__name__)",
                        "from flask import",
                        "from django",
                        "if __name__ == '__main__':"
                    ]):
                        return file
            except:
                continue
    
    return None

def run_application(main_file):
    """Run the application with proper port binding"""
    print(f"🚀 Starting Django application: {main_file}")
    
    # Set environment variables for Replit compatibility
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "5000"
    
    try:
        # For Django applications, use runserver command
        if main_file == "manage.py":
            print("🌐 Starting Django development server...")
            subprocess.run([sys.executable, "manage.py", "runserver", "0.0.0.0:5000"], check=True)
        else:
            # Try to run the application
            subprocess.run([sys.executable, main_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        sys.exit(0)

def main():
    """Main startup function"""
    print("🔍 Looking for application entry point...")
    
    # First, ensure deployment has run
    if not any(os.path.exists(f) for f in ["main.py", "app.py", "requirements.txt", ".git"]):
        print("📥 Repository not found. Running deployment first...")
        try:
            subprocess.run([sys.executable, "deploy.py"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Deployment failed")
            sys.exit(1)
    
    main_file = find_main_file()
    
    if main_file:
        print(f"✅ Found entry point: {main_file}")
        run_application(main_file)
    else:
        print("❌ No suitable entry point found")
        print("📋 Available Python files:")
        for file in os.listdir("."):
            if file.endswith(".py"):
                print(f"  - {file}")
        print("\n🔧 Please run one of the above files manually:")
        print("   python <filename>")

if __name__ == "__main__":
    main()
