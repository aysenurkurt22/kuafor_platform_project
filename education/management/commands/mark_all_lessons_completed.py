from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from education.models import Lesson, UserLessonProgress
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Belirtilen kullanıcı için tüm dersleri tamamlandı olarak işaretler.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Dersleri tamamlanacak kullanıcının kullanıcı adı.')

    def handle(self, *args, **kwargs):
        username_to_update = kwargs['username']
        self.stdout.write(self.style.SUCCESS(f"Kullanıcı '{username_to_update}' için dersler tamamlandı olarak işaretleniyor..."))

        try:
            user = User.objects.get(username=username_to_update)
            lessons = Lesson.objects.all()
            updated_count = 0
            for lesson in lessons:
                progress, created = UserLessonProgress.objects.get_or_create(
                    user=user,
                    lesson=lesson,
                    defaults={'completed': True, 'completion_date': timezone.now()}
                )
                if not progress.completed:
                    progress.completed = True
                    progress.completion_date = timezone.now()
                    progress.save()
                    updated_count += 1
                    self.stdout.write(f"Ders '{lesson.title}' tamamlandı olarak işaretlendi.")
                elif created:
                    self.stdout.write(f"Ders '{lesson.title}' tamamlandı olarak oluşturuldu.")
                else:
                    self.stdout.write(f"Ders '{lesson.title}' zaten tamamlanmış.")
            
            self.stdout.write(self.style.SUCCESS(f"Toplam {updated_count} ders güncellendi/işaretlendi."))
            logger.info(f"Kullanıcı '{username_to_update}' için toplam {updated_count} ders güncellendi/işaretlendi.")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Hata: '{username_to_update}' kullanıcı adında bir kullanıcı bulunamadı."))
            logger.error(f"Hata: '{username_to_update}' kullanıcı adında bir kullanıcı bulunamadı.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Beklenmedik bir hata oluştu: {e}"))
            logger.error(f"Beklenmedik bir hata oluştu: {e}")