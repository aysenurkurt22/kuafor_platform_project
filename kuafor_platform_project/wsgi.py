import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise # Whitenoise import edildi

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuafor_platform_project.settings')

application = get_wsgi_application()
application = DjangoWhiteNoise(application) # Whitenoise uygulandı