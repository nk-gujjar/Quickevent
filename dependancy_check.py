import subprocess
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_install_dependencies():
    """Check for required dependencies and install them if missing."""
    required_packages = [
        'google-api-python-client',
        'google-auth',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'pytz',
        'groq'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Try to find the package name that would be used in import statements
            import_name = package.replace('-', '_').split('>=')[0].split('==')[0]
            importlib.import_module(import_name.split('[')[0])
            logger.info(f"Package {package} is already installed")
        except ImportError:
            logger.warning(f"Package {package} is missing, will install")
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logger.info("All missing packages installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install packages: {e}")
            return False
    
    return True