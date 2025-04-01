import os
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Get the templates directory path
template_dir = Path(__file__).parent.parent / "templates"

# Create Jinja2 environment
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

def renderTemplate(template_name, **context):
    """
    Render a template with the given context
    """
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {str(e)}")
        # Fallback to a simple message if template rendering fails
        return f"<html><body><h1>Error rendering template</h1><p>{str(e)}</p></body></html>"