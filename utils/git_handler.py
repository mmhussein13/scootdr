import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def clone_repository(repo_url, target_directory):
    """
    Clone the Git repository at repo_url into the target_directory.
    
    Args:
        repo_url (str): URL of the Git repository
        target_directory (str): Local directory where to clone the repository
    
    Returns:
        bool: True if successful, raises exception otherwise
    """
    logger.debug(f"Cloning repository {repo_url} to {target_directory}")
    
    try:
        # Make sure the target directory exists
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
        
        # Clone the repository
        process = subprocess.run(
            ['git', 'clone', repo_url, target_directory],
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.debug(f"Git clone output: {process.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git clone failed: {e.stderr or str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    except Exception as e:
        error_msg = f"Failed to clone repository: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
