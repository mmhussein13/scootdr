#!/usr/bin/env python3
"""
Deployment script for scootdr repository
Clones the repository and sets up the environment
"""

import os
import subprocess
import sys
import shutil

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"✓ {command}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running: {command}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def main():
    """Main deployment function"""
    repo_url = "https://github.com/mmhussein13/scootdr.git"
    repo_name = "scootdr"
    
    print("🚀 Starting scootdr deployment...")
    
    # Check if repository already exists
    if os.path.exists(repo_name):
        print(f"📁 Repository '{repo_name}' already exists. Removing...")
        shutil.rmtree(repo_name)
    
    # Clone the repository
    print(f"📥 Cloning repository from {repo_url}...")
    if not run_command(f"git clone {repo_url}"):
        print("❌ Failed to clone repository")
        sys.exit(1)
    
    # Check if requirements.txt exists
    requirements_path = os.path.join(repo_name, "requirements.txt")
    if not os.path.exists(requirements_path):
        print("⚠️  requirements.txt not found in repository")
        print("📋 Listing repository contents:")
        run_command("ls -la", cwd=repo_name)
    else:
        print("📋 Found requirements.txt, installing dependencies...")
        if not run_command(f"pip install -r requirements.txt", cwd=repo_name):
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Copy repository contents to current directory
    print("📂 Moving repository contents to current directory...")
    for item in os.listdir(repo_name):
        src = os.path.join(repo_name, item)
        dst = item
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    
    # Remove the cloned directory
    shutil.rmtree(repo_name)
    
    # Check for common Python entry points
    entry_points = ["main.py", "app.py", "server.py", "run.py", "manage.py"]
    found_entry = None
    
    for entry in entry_points:
        if os.path.exists(entry):
            found_entry = entry
            break
    
    if found_entry:
        print(f"🎯 Found entry point: {found_entry}")
    else:
        print("📋 Available Python files:")
        for file in os.listdir("."):
            if file.endswith(".py"):
                print(f"  - {file}")
    
    print("✅ Deployment completed successfully!")
    print("🔧 To start the application, run: python start.py")

if __name__ == "__main__":
    main()
