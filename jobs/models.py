from django.db import models
from users.models import CustomUser

class JobPosting(models.Model):
    employer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary_expectation = models.CharField(max_length=100, blank=True, null=True)
    employment_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
    ])
    skills_required = models.TextField(help_text="Comma separated skills")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title