from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify # Slug için

class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True) # SEO için
    description = models.TextField()
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='taught_courses')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True) # Kurs görseli

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('education:course_detail', kwargs={'slug': self.slug, 'pk': self.pk})

    def __str__(self):
        return self.title

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0) # Bölüm sırası

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order') # Bir kursta bölüm sırası benzersiz olmalı

    def __str__(self):
        return f"{self.course.title} - Bölüm {self.order}: {self.title}"

class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Metin'),
        ('quiz', 'Quiz'),
    ]
    section = models.ForeignKey('Section', on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES)
    content_video_url = models.URLField(max_length=500, blank=True, null=True) # Video dersler için
    content_text = models.TextField(blank=True, null=True) # Metin dersler için
    order = models.PositiveIntegerField(default=0) # Ders sırası

    class Meta:
        ordering = ['order']
        unique_together = ('section', 'order') # Bir bölümde ders sırası benzersiz olmalı

    def __str__(self):
        return f"{self.section.course.title} - Ders {self.order}: {self.title}"

class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Quiz: {self.title}"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    
    def __str__(self):
        return self.text[:50]

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:50]

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course') # Bir kullanıcı bir kursa sadece bir kez kayıt olabilir

    def __str__(self):
        return f"{self.user.username} - {self.course.title} Kayıt"

class UserLessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} İlerleme"