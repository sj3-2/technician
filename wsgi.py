# wsgi.py - PythonAnywhere WSGI configuration
import sys
import os

# Add your project directory to sys.path
path = '/home/yourusername/technician'  # Update this with your actual username
if path not in sys.path:
    sys.path.append(path)

from app import app as application

if __name__ == "__main__":
    application.run()
