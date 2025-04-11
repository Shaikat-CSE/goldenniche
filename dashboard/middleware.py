import re
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from .models import Activity

class ActivityTrackingMiddleware:
    """Middleware to track user activities in the dashboard"""
    
    IGNORED_PATHS = [
        r'^/static/',
        r'^/media/',
        r'^/dashboard/api/',
        r'^/favicon\.ico$',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.ignored_paths_regex = [re.compile(path) for path in self.IGNORED_PATHS]
    
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        # Process the response
        self.log_activity(request, response)
        
        return response
        
    def log_activity(self, request, response):
        """Log user activity"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return
            
        # Skip logging for ignored paths
        if any(regex.match(request.path) for regex in self.ignored_paths_regex):
            return
            
        # Skip logging for non-dashboard paths
        if not request.path.startswith('/dashboard/'):
            return
            
        # Get information from the request
        user = request.user
        path = request.path
        method = request.method
        
        # Determine the action based on request method
        if method == 'GET':
            action = 'view'
        elif method == 'POST' and 'delete' in path:
            action = 'delete'
        elif method == 'POST' and 'create' in path:
            action = 'create'
        elif method == 'POST' and any(x in path for x in ['edit', 'update']):
            action = 'update'
        else:
            action = 'other'
            
        # Get entity type from path
        entity_type = None
        entity_id = None
        
        # Extract entity type from path
        path_parts = path.strip('/').split('/')
        if len(path_parts) > 1 and path_parts[0] == 'dashboard':
            if len(path_parts) > 1:
                entity_type = path_parts[1]
                
            # Try to extract entity ID if available
            if len(path_parts) > 2 and path_parts[2].isdigit():
                entity_id = path_parts[2]
                
        if entity_type:
            # Create activity record
            description = f"{action.capitalize()} {entity_type}"
            if entity_id:
                description += f" (ID: {entity_id})"
                
            # Get IP address with X-Forwarded-For support
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', None)
            if ip_address:
                # X-Forwarded-For can include multiple IPs, get the client IP
                ip_address = ip_address.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', None)
                
            try:
                Activity.objects.create(
                    user=user,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    description=description,
                    ip_address=ip_address
                )
            except Exception as e:
                # Log the error but don't crash the middleware
                print(f"Error logging activity: {e}")
                
    # For async support
    async def __acall__(self, request):
        response = await self.get_response(request)
        # We don't log activity in async context to avoid sync/async issues
        # This could be implemented properly with async ORM operations if needed 