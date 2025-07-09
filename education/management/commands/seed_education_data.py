from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from education.models import Course, Section, Lesson, Quiz, Question, Answer
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Eğitim platformu için örnek kurs, bölüm, ders ve quiz verileri ekler.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Örnek eğitim verileri ekleniyor...'))

        try:
            instructor = User.objects.get(username='egitmen')
        except User.DoesNotExist:
            instructor = User.objects.create_user(username='egitmen', email='egitmen@example.com', password='password123', is_staff=True)
            self.stdout.write(self.style.SUCCESS('Eğitmen kullanıcısı oluşturuldu: egitmen'))

        course1, created = Course.objects.get_or_create(
            title='Kuaförlük Temelleri: Başlangıç Rehberi',
            defaults={
                'description': 'Bu kurs, kuaförlük mesleğine yeni başlayanlar için temel bilgileri ve teknikleri kapsar.',
                'instructor': instructor,
                'price': 0.00,
                'is_published': True,
                'slug': slugify('Kuaförlük Temelleri: Başlangıç Rehberi')
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Kurs oluşturuldu: {course1.title}'))
        
        section1_1, created = Section.objects.get_or_create(
            course=course1,
            title='Giriş ve Temel Bilgiler',
            order=1,
            defaults={'course': course1}
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Bölüm oluşturuldu: {section1_1.title}'))

        lesson1_1_1, created = Lesson.objects.get_or_create(
            section=section1_1,
            title='Kuaförlüğe Giriş',
            order=1,
            defaults={
                'lesson_type': 'text',
                'content_text': 'Kuaförlük mesleğinin tarihi, önemi ve temel prensipleri.',
                'section': section1_1
            }
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Ders oluşturuldu: {lesson1_1_1.title}'))

        lesson1_1_2, created = Lesson.objects.get_or_create(
            section=section1_1,
            title='Hijyen ve Güvenlik',
            order=2,
            defaults={
                'lesson_type': 'video',
                'content_video_url': 'https://www.youtube.com/watch?v=KjsEtDHzBns',
                'section': section1_1
            }
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Ders oluşturuldu: {lesson1_1_2.title}'))

        section1_2, created = Section.objects.get_or_create(
            course=course1,
            title='Saç Kesim Teknikleri',
            order=2,
            defaults={'course': course1}
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Bölüm oluşturuldu: {section1_2.title}'))

        lesson1_2_1, created = Lesson.objects.get_or_create(
            section=section1_2,
            title='Temel Kat Kesimi',
            order=1,
            defaults={
                'lesson_type': 'text',
                'content_text': 'Kat kesiminin adımları ve dikkat edilmesi gerekenler.',
                'section': section1_2
            }
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Ders oluşturuldu: {lesson1_2_1.title}'))

        lesson1_2_2, created = Lesson.objects.get_or_create(
            section=section1_2,
            title='Saç Kesim Quizi',
            order=2,
            defaults={
                'lesson_type': 'quiz',
                'section': section1_2
            }
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Ders oluşturuldu: {lesson1_2_2.title}'))

        if lesson1_2_2:
            quiz1, created = Quiz.objects.get_or_create(
                lesson=lesson1_2_2,
                defaults={
                    'title': 'Saç Kesim Temelleri Quizi',
                    'description': 'Saç kesim teknikleri bilginizi test edin.'
                }
            )
            if created: self.stdout.write(self.style.SUCCESS(f'Quiz oluşturuldu: {quiz1.title}'))

            if quiz1:
                q1, created = Question.objects.get_or_create(
                    quiz=quiz1,
                    text='Hangi kesim tekniği saça hacim kazandırır?',
                    defaults={'quiz': quiz1}
                )
                if created:
                    Answer.objects.get_or_create(question=q1, text='Düz kesim', is_correct=False)
                    Answer.objects.get_or_create(question=q1, text='Katlı kesim', is_correct=True)
                    Answer.objects.get_or_create(question=q1, text='Küt kesim', is_correct=False)
                    Answer.objects.get_or_create(question=q1, text='Asimetrik kesim', is_correct=False)
                    self.stdout.write(self.style.SUCCESS(f'Soru ve cevaplar oluşturuldu: {q1.text}'))

                q2, created = Question.objects.get_or_create(
                    quiz=quiz1,
                    text='Saç kesiminde kullanılan temel aletlerden biri değildir?',
                    defaults={'quiz': quiz1}
                )
                if created:
                    Answer.objects.get_or_create(question=q2, text='Makas', is_correct=False)
                    Answer.objects.get_or_create(question=q2, text='Tarak', is_correct=False)
                    Answer.objects.get_or_create(question=q2, text='Fön makinesi', is_correct=True)
                    Answer.objects.get_or_create(question=q2, text='Ustura', is_correct=False)
                    self.stdout.write(self.style.SUCCESS(f'Soru ve cevaplar oluşturuldu: {q2.text}'))

        course2, created = Course.objects.get_or_create(
            title='Saç Boyama Sanatı: İleri Teknikler',
            defaults={
                'description': 'Bu kurs, saç boyama konusunda ileri düzey teknikleri ve renk teorisini öğretir.',
                'instructor': instructor,
                'price': 149.99,
                'is_published': True,
                'slug': slugify('Saç Boyama Sanatı: İleri Teknikler')
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Kurs oluşturuldu: {course2.title}'))

        section2_1, created = Section.objects.get_or_create(
            course=course2,
            title='Renk Teorisi ve Uygulamaları',
            order=1,
            defaults={'course': course2}
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Bölüm oluşturuldu: {section2_1.title}'))

        lesson2_1_1, created = Lesson.objects.get_or_create(
            section=section2_1,
            title='Ana Renkler ve Karışımları',
            order=1,
            defaults={
                'lesson_type': 'text',
                'content_text': 'Renk çarkı, ana renkler, ara renkler ve tamamlayıcı renkler hakkında detaylı bilgi.',
                'section': section2_1
            }
        )
        if created: self.stdout.write(self.style.SUCCESS(f'Ders oluşturuldu: {lesson2_1_1.title}'))

        self.stdout.write(self.style.SUCCESS('Örnek eğitim verileri başarıyla eklendi.'))
