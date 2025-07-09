from django.core.management.base import BaseCommand
from shop.models import Product
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Mevcut ürünlerin slug alanlarını doldurur.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Ürün slug alanları kontrol ediliyor ve dolduruluyor...'))
        
        products = Product.objects.all()
        updated_count = 0
        for product in products:
            if not product.slug:
                product.slug = slugify(product.name)
                product.save()
                self.stdout.write(f"Ürün '{product.name}' için slug oluşturuldu: {product.slug}")
                logger.info(f"Ürün '{product.name}' için slug oluşturuldu: {product.slug}")
                updated_count += 1
            else:
                self.stdout.write(f"Ürün '{product.name}' zaten bir slug'a sahip: {product.slug}")
        
        self.stdout.write(self.style.SUCCESS(f"Tüm ürünlerin slug alanları kontrol edildi. {updated_count} ürün güncellendi."))
        logger.info(f"Tüm ürünlerin slug alanları kontrol edildi. {updated_count} ürün güncellendi.")