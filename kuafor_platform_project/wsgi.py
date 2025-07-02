import os

from django.core.wsgi import get_wsgi_application
from whitenoise.middleware import WhiteNoise # Whitenoise'ın yeni import yolu

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuafor_platform_project.settings')

application = get_wsgi_application()
application = WhiteNoise(application) # Whitenoise'ın yeni kullanım şekli
