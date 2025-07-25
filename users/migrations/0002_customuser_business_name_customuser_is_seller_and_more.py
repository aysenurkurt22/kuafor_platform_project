# Generated by Django 5.2.3 on 2025-07-06 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='business_name',
            field=models.CharField(blank=True, help_text='İşletme adı', max_length=200, null=True),
        ),
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
        migrations.AddField(
            model_name='customuser',
            name='tax_number',
            field=models.CharField(blank=True, help_text='Vergi numarası', max_length=50, null=True),
        ),
    ]
