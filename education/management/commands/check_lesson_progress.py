from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from education.models import Course, Section, Lesson, UserLessonProgress
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Belirtilen kullanıcının ders ilerleme kayıtlarını kontrol eder ve yazdırır.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='İlerlemesi kontrol edilecek kullanıcının kullanıcı adı.')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        self.stdout.write(self.style.SUCCESS(f"Kullanıcı '{username}' için ders ilerlemesi kontrol ediliyor..."))

        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"Kullanıcı: {user.username} (ID: {user.id})")
            
            all_progress = UserLessonProgress.objects.filter(user=user)
            if all_progress.exists():
                self.stdout.write("\nKullanıcının Ders İlerleme Kayıtları:")
                for progress in all_progress:
                    self.stdout.write(f"- Ders: {progress.lesson.title}, Tamamlandı: {progress.completed}")
            else:
                self.stdout.write("\nKullanıcının hiç ders ilerleme kaydı bulunamadı.")
            
            first_course = Course.objects.first()
            if first_course:
                self.stdout.write(f"\n'{first_course.title}' kursunun dersleri ve ilerleme durumu:")
                for section in first_course.sections.all().order_by('order'):
                    for lesson in section.lessons.all().order_by('order'):
                        lesson_progress = UserLessonProgress.objects.filter(user=user, lesson=lesson).first()
                        completed_status = lesson_progress.completed if lesson_progress else False
                        self.stdout.write(f"- Ders: {lesson.title}, Tamamlandı (DB): {completed_status}")
            else:
                self.stdout.write("\nHiç kurs bulunamadı.")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Hata: '{username}' kullanıcı adında bir kullanıcı bulunamadı."))
            logger.error(f"Hata: '{username}' kullanıcı adında bir kullanıcı bulunamadı.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Beklenmedik bir hata oluştu: {e}"))
            logger.error(f"Beklenmedik bir hata oluştu: {e}")