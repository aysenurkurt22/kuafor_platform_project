# users/migrations/0003_auto_20250707_0119.py dosyasını bu şekilde değiştirin:

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_customuser_business_name_customuser_is_seller_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_seller',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='seller_verified',
            field=models.BooleanField(default=False, help_text='Satıcı doğrulaması'),
        ),
        # business_name ve tax_number zaten var, eklemeye gerek yok
    ]