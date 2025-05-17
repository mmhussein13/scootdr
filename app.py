import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import tempfile
import shutil
from utils.git_handler import clone_repository
from utils.django_analyzer import analyze_django_project

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Global variables to store repository data
REPO_URL = "https://github.com/mmhussein13/scootdr.git"
TEMP_DIR = None
PROJECT_DATA = None

@app.route('/')
def index():
    """Main page that initiates repository cloning and analysis"""
    global TEMP_DIR, PROJECT_DATA
    
    # Clean up any existing temp directory
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            logger.debug(f"Cleaned up previous temp directory: {TEMP_DIR}")
        except Exception as e:
            logger.error(f"Error cleaning up directory: {e}")
    
    # Create a new temp directory
    TEMP_DIR = tempfile.mkdtemp()
    logger.debug(f"Created new temp directory: {TEMP_DIR}")
    
    # Clone the repository
    try:
        clone_repository(REPO_URL, TEMP_DIR)
        logger.info(f"Successfully cloned repository to {TEMP_DIR}")
        flash("Repository cloned successfully!", "success")
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        flash(f"Error cloning repository: {str(e)}", "danger")
        return render_template('flask_index.html', error=str(e))
    
    # Analyze the Django project
    try:
        PROJECT_DATA = analyze_django_project(TEMP_DIR)
        logger.info("Django project analysis completed")
    except Exception as e:
        logger.error(f"Error analyzing Django project: {e}")
        flash(f"Error analyzing project: {str(e)}", "danger")
        return render_template('flask_index.html', error=str(e))
    
    return render_template('flask_index.html', project_data=PROJECT_DATA, repo_url=REPO_URL)

@app.route('/file/<path:file_path>')
def view_file(file_path):
    """View the contents of a specific file"""
    global TEMP_DIR
    
    if not TEMP_DIR or not os.path.exists(TEMP_DIR):
        flash("Repository not cloned or temporary directory not found", "danger")
        return redirect(url_for('index'))
    
    # Build the absolute path to the file
    full_path = os.path.join(TEMP_DIR, file_path)
    
    # Check if the path exists and is a file
    if not os.path.exists(full_path):
        flash(f"File not found: {file_path}", "danger")
        return redirect(url_for('index'))
    
    if not os.path.isfile(full_path):
        flash(f"Path is not a file: {file_path}", "danger")
        return redirect(url_for('index'))
    
    # Read the file content
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        content = "Binary file - cannot display content"
    except Exception as e:
        flash(f"Error reading file: {str(e)}", "danger")
        return redirect(url_for('index'))
    
    file_info = {
        'path': file_path,
        'content': content,
        'extension': os.path.splitext(file_path)[1].lower()
    }
    
    return render_template('flask_file_viewer.html', file_info=file_info, project_data=PROJECT_DATA, repo_url=REPO_URL)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('flask_index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('flask_index.html', error="Internal server error"), 500

# Clean up temp directory when the app exits
def cleanup():
    global TEMP_DIR
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        logger.debug(f"Cleaned up temp directory on exit: {TEMP_DIR}")

import atexit
atexit.register(cleanup)
