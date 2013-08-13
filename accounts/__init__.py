import os

VERSION = '0.3'

# Setting for template directory not found by app_directories.Loader.  This
# allows templates to be identified by two paths which enables a template to be
# extended by a template with the same identifier.
TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'templates/oscar')
