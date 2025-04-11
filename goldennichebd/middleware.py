import re

class StaticFilesCacheMiddleware:
    """
    Middleware that sets Cache-Control headers for static files.
    This ensures browsers properly cache and render images and other static files.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Compile regex patterns for file types
        self.is_image = re.compile(r'\.(jpg|jpeg|png|gif|svg|webp|ico)$', re.IGNORECASE)
        self.is_css_js = re.compile(r'\.(css|js)$', re.IGNORECASE)
        self.is_font = re.compile(r'\.(woff|woff2|ttf|eot|otf)$', re.IGNORECASE)
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Get the path from the request
        path = request.path.lower()
        
        # Only set Cache-Control headers for static files
        if '/static/' in path or '/media/' in path:
            if self.is_image.search(path):
                # Cache images for 1 week
                response['Cache-Control'] = 'public, max-age=604800'
                # Add content-type header for SVG files if needed
                if path.endswith('.svg'):
                    response['Content-Type'] = 'image/svg+xml'
            elif self.is_css_js.search(path):
                # Cache CSS and JS files for 1 day
                response['Cache-Control'] = 'public, max-age=86400'
            elif self.is_font.search(path):
                # Cache font files for 1 week
                response['Cache-Control'] = 'public, max-age=604800'
                # Add CORS headers for fonts (needed for some browsers)
                response['Access-Control-Allow-Origin'] = '*'
            else:
                # Default cache for other static files - 1 hour
                response['Cache-Control'] = 'public, max-age=3600'
        
        return response 