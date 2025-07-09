from django.db import models
from django.conf import settings

from django.urls import reverse

class JobPosting(models.Model):
    EMPLOYMENT_TYPE_CHOICES = (
        ('full-time', 'Tam Zamanlı'),
        ('part-time', 'Yarı Zamanlı'),
        ('contract', 'Sözleşmeli'),
        ('freelance', 'Serbest Çalışma'),
        ('internship', 'Staj'),
    )
    EMPLOYMENT_TYPE_CHOICES = (
        ('full-time', 'Tam Zamanlı'),
        ('part-time', 'Yarı Zamanlı'),
        ('contract', 'Sözleşmeli'),
        ('freelance', 'Serbest Çalışma'),
        ('internship', 'Staj'),
    )
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True, null=True)
    salary_expectation = models.CharField(max_length=100, blank=True, null=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full-time')
    skills_required = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    highlighted = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False) 

    def get_absolute_url(self):
        return reverse('jobs:job_post_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Beklemede'),
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi'),
    )
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    class Meta:
        unique_together = ('job_posting', 'applicant')
        ordering = ('-application_date',)

    def __str__(self):
        return f'{self.applicant.username} - {self.job_posting.title}'
