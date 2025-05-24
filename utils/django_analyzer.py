import os
import json
import logging
import re

logger = logging.getLogger(__name__)

def analyze_django_project(project_dir):
    """
    Analyze a Django project directory and extract key information about its structure.
    
    Args:
        project_dir (str): Path to the Django project directory
    
    Returns:
        dict: Information about the Django project structure
    """
    logger.debug(f"Analyzing Django project in {project_dir}")
    
    # Result structure
    project_data = {
        'project_name': os.path.basename(project_dir),
        'django_apps': [],
        'settings': {},
        'urls': {},
        'models': {},
        'views': {},
        'templates': [],
        'static_files': [],
        'requirements': [],
        'database_info': {},
        'file_structure': []
    }
    
    # Generate file structure
    project_data['file_structure'] = get_file_structure(project_dir)
    
    # Find Django apps
    project_data['django_apps'] = find_django_apps(project_dir)
    
    # Analyze settings
    settings_file = find_settings_file(project_dir)
    if settings_file:
        project_data['settings'] = analyze_settings(settings_file)
    
    # Get requirements
    requirements_file = os.path.join(project_dir, 'requirements.txt')
    if os.path.exists(requirements_file):
        project_data['requirements'] = extract_requirements(requirements_file)
    
    # Analyze models and views for each app
    for app in project_data['django_apps']:
        app_dir = os.path.join(project_dir, app)
        
        # Models
        models_file = os.path.join(app_dir, 'models.py')
        if os.path.exists(models_file):
            project_data['models'][app] = extract_models(models_file)
        
        # Views
        views_file = os.path.join(app_dir, 'views.py')
        if os.path.exists(views_file):
            project_data['views'][app] = extract_views(views_file)
        
        # URLs
        urls_file = os.path.join(app_dir, 'urls.py')
        if os.path.exists(urls_file):
            project_data['urls'][app] = extract_urls(urls_file)
    
    # Find templates
    project_data['templates'] = find_templates(project_dir)
    
    # Find static files
    project_data['static_files'] = find_static_files(project_dir)
    
    logger.info(f"Django project analysis completed. Found {len(project_data['django_apps'])} apps.")
    return project_data

def get_file_structure(directory, prefix=''):
    """Generate a list of all files in the directory structure"""
    files = []
    
    try:
        for item in os.listdir(directory):
            # Skip .git folder
            if item == '.git':
                continue
                
            path = os.path.join(directory, item)
            rel_path = os.path.join(prefix, item)
            
            if os.path.isfile(path):
                files.append({
                    'path': rel_path,
                    'type': 'file',
                    'extension': os.path.splitext(item)[1].lower()
                })
            elif os.path.isdir(path):
                files.append({
                    'path': rel_path,
                    'type': 'directory',
                    'children': get_file_structure(path, rel_path)
                })
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
    
    return files

def find_django_apps(project_dir):
    """Identify Django applications within the project"""
    django_apps = []
    
    try:
        for item in os.listdir(project_dir):
            potential_app_dir = os.path.join(project_dir, item)
            
            # Check if it's a directory
            if not os.path.isdir(potential_app_dir):
                continue
            
            # Check for typical Django app files
            has_init = os.path.exists(os.path.join(potential_app_dir, '__init__.py'))
            has_models = os.path.exists(os.path.join(potential_app_dir, 'models.py'))
            has_views = os.path.exists(os.path.join(potential_app_dir, 'views.py'))
            has_apps = os.path.exists(os.path.join(potential_app_dir, 'apps.py'))
            
            # If it has at least 2 of these files, consider it a Django app
            if has_init and (has_models or has_views or has_apps):
                django_apps.append(item)
    except Exception as e:
        logger.error(f"Error finding Django apps: {e}")
    
    return django_apps

def find_settings_file(project_dir):
    """Find the Django settings.py file"""
    # Check for settings.py in the root
    settings_file = os.path.join(project_dir, 'settings.py')
    if os.path.exists(settings_file):
        return settings_file
    
    # Check for settings.py in subdirectories
    for item in os.listdir(project_dir):
        potential_dir = os.path.join(project_dir, item)
        if os.path.isdir(potential_dir):
            settings_file = os.path.join(potential_dir, 'settings.py')
            if os.path.exists(settings_file):
                return settings_file
    
    return None

def analyze_settings(settings_file):
    """Extract key information from Django settings.py"""
    settings_info = {
        'installed_apps': [],
        'database_engine': 'Unknown',
        'middleware': [],
        'template_dirs': [],
        'static_dirs': [],
    }
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract INSTALLED_APPS
            apps_match = re.search(r'INSTALLED_APPS\s*=\s*\[([^\]]*)\]', content, re.DOTALL)
            if apps_match:
                apps_text = apps_match.group(1)
                apps = re.findall(r'[\'"]([^\'"]+)[\'"]', apps_text)
                settings_info['installed_apps'] = apps
            
            # Extract DATABASE info
            db_match = re.search(r'DATABASES\s*=\s*{[^}]*\'ENGINE\':\s*[\'"]([^\'"]+)[\'"]', content, re.DOTALL)
            if db_match:
                settings_info['database_engine'] = db_match.group(1)
            
            # Extract MIDDLEWARE
            middleware_match = re.search(r'MIDDLEWARE\s*=\s*\[([^\]]*)\]', content, re.DOTALL)
            if middleware_match:
                middleware_text = middleware_match.group(1)
                middleware = re.findall(r'[\'"]([^\'"]+)[\'"]', middleware_text)
                settings_info['middleware'] = middleware
            
            # Extract TEMPLATE DIRS
            template_match = re.search(r'TEMPLATES\s*=\s*\[.*?\'DIRS\':\s*\[([^\]]*)\]', content, re.DOTALL)
            if template_match:
                template_text = template_match.group(1)
                templates = re.findall(r'[\'"]([^\'"]+)[\'"]', template_text)
                settings_info['template_dirs'] = templates
            
            # Extract STATIC_DIRS
            static_match = re.search(r'STATICFILES_DIRS\s*=\s*\[([^\]]*)\]', content, re.DOTALL)
            if static_match:
                static_text = static_match.group(1)
                statics = re.findall(r'[\'"]([^\'"]+)[\'"]', static_text)
                settings_info['static_dirs'] = statics
    
    except Exception as e:
        logger.error(f"Error analyzing settings file {settings_file}: {e}")
    
    return settings_info

def extract_requirements(requirements_file):
    """Parse requirements.txt file"""
    requirements = []
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    except Exception as e:
        logger.error(f"Error reading requirements file: {e}")
    
    return requirements

def extract_models(models_file):
    """Extract model classes from models.py"""
    models = []
    
    try:
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find model classes (inheriting from models.Model)
            model_matches = re.finditer(r'class\s+(\w+)\s*\([^)]*models\.Model[^)]*\):', content)
            
            for match in model_matches:
                model_name = match.group(1)
                model_info = {
                    'name': model_name,
                    'fields': []
                }
                
                # Find the start position of the model class
                start_pos = match.end()
                
                # Find fields of this model class
                field_pattern = r'(\w+)\s*=\s*models\.([A-Za-z]+)\(([^)]*)\)'
                field_matches = re.finditer(field_pattern, content[start_pos:])
                
                for field_match in field_matches:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    field_args = field_match.group(3).strip()
                    
                    # Stop if we encounter another class definition
                    if field_name == 'class':
                        break
                    
                    model_info['fields'].append({
                        'name': field_name,
                        'type': field_type,
                        'args': field_args
                    })
                
                models.append(model_info)
    
    except Exception as e:
        logger.error(f"Error extracting models from {models_file}: {e}")
    
    return models

def extract_views(views_file):
    """Extract view functions and classes from views.py"""
    views = []
    
    try:
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find view functions
            function_matches = re.finditer(r'def\s+(\w+)\s*\([^)]*\):', content)
            for match in function_matches:
                view_name = match.group(1)
                # Skip if it's likely a helper function, not a view
                if not view_name.startswith('_'):
                    views.append({
                        'name': view_name,
                        'type': 'function'
                    })
            
            # Find class-based views
            class_matches = re.finditer(r'class\s+(\w+)(?:View)?\s*\(([^)]*)\):', content)
            for match in class_matches:
                view_name = match.group(1)
                parent_classes = match.group(2).split(',')
                parent_classes = [p.strip() for p in parent_classes]
                
                views.append({
                    'name': view_name,
                    'type': 'class',
                    'parent_classes': parent_classes
                })
    
    except Exception as e:
        logger.error(f"Error extracting views from {views_file}: {e}")
    
    return views

def extract_urls(urls_file):
    """Extract URL patterns from urls.py"""
    urls = []
    
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find urlpatterns section
            urlpatterns_match = re.search(r'urlpatterns\s*=\s*\[([^\]]*)\]', content, re.DOTALL)
            if not urlpatterns_match:
                return urls
            
            urlpatterns_text = urlpatterns_match.group(1)
            
            # Extract individual URL patterns
            pattern_matches = re.finditer(r'path\s*\(\s*[\'"]([^\'"]*)[\'"],\s*([^,]*),\s*(?:name\s*=\s*[\'"]([^\'"]*)[\'"])?\s*\)', urlpatterns_text)
            
            for match in pattern_matches:
                path = match.group(1)
                view = match.group(2).strip()
                name = match.group(3) if match.group(3) else "unnamed"
                
                urls.append({
                    'path': path,
                    'view': view,
                    'name': name
                })
    
    except Exception as e:
        logger.error(f"Error extracting URLs from {urls_file}: {e}")
    
    return urls

def find_templates(project_dir):
    """Find template files within the project"""
    templates = []
    
    template_dirs = ['templates']  # Default template directory
    
    try:
        # Walk through all directories
        for root, dirs, files in os.walk(project_dir):
            # Skip .git directory
            if '.git' in root:
                continue
                
            # Check if this is a template directory
            if os.path.basename(root) == 'templates' or any(td in root for td in template_dirs):
                for file in files:
                    if file.endswith(('.html', '.htm', '.xml')):
                        rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                        templates.append(rel_path)
    
    except Exception as e:
        logger.error(f"Error finding templates: {e}")
    
    return templates

def find_static_files(project_dir):
    """Find static files within the project"""
    static_files = []
    
    static_dirs = ['static']  # Default static directory
    
    try:
        # Walk through all directories
        for root, dirs, files in os.walk(project_dir):
            # Skip .git directory
            if '.git' in root:
                continue
                
            # Check if this is a static directory
            if os.path.basename(root) == 'static' or any(sd in root for sd in static_dirs):
                for file in files:
                    if file.endswith(('.css', '.js', '.svg')):
                        rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                        static_files.append({
                            'path': rel_path,
                            'type': os.path.splitext(file)[1][1:]  # Extension without the dot
                        })
    
    except Exception as e:
        logger.error(f"Error finding static files: {e}")
    
    return static_files
