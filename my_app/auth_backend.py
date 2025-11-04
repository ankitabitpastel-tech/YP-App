from django.contrib.auth.backends import BaseBackend
from .models import user

class CustomUserAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, email=None):
        try: 
            if email:
                user_obj = user.objects.get(email=email, status='1')
            else:
                user_obj = user.objects.get(username=username, status='1')

                if user_obj.check_password(password) and user_obj.role == '0':
                    return user_obj
        except user.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return user.objects.get(pk=user_id, status__in='1'/'0')
        except user.DoesNotExist:
            return None