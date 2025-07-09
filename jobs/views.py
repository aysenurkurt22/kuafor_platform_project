from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import JobPosting, Application
from .forms import JobPostingForm
from memberships.models import UserMembership, MembershipPlan
from django.contrib import messages
from datetime import datetime
from users.models import CustomUser
from users.decorators import employer_required, customer_required
from notifications.models import Notification
from django.utils.translation import gettext_lazy as _

@login_required
@employer_required
def job_post_create(request):
    user_membership = request.user.user_membership
    current_month_job_postings = JobPosting.objects.filter(
        employer=request.user,
        created_at__year=datetime.now().year,
        created_at__month=datetime.now().month
    ).count()

    max_postings_from_plan = 0
    if user_membership and user_membership.is_active:
        max_postings_from_plan = user_membership.membership_plan.max_job_postings
    elif not user_membership or user_membership.membership_plan.membership_type == 'FREE':
        max_postings_from_plan = 1 # Free plan limit

    can_post_via_plan = (max_postings_from_plan == 0) or (current_month_job_postings < max_postings_from_plan)
    can_post_via_credits = request.user.extra_job_posting_credits > 0

    if not can_post_via_plan and not can_post_via_credits:
        messages.error(request, f"Bu ay için ilan limitinizi doldurdunuz ve ek ilan krediniz bulunmamaktadır. Üyeliğinizi yükselterek veya ürün satın alarak daha fazla ilan yayınlayabilirsiniz.")
        return redirect('jobs:job_post_list')

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_post = form.save(commit=False)
            job_post.employer = request.user
            # Basic spam check for job posting
            spam_keywords = ['work from home scam', 'easy money', 'guaranteed income', 'fast cash', 'no experience needed', 'urgent hiring']
            is_spam = False
            for keyword in spam_keywords:
                if keyword in job_post.title.lower() or keyword in job_post.description.lower():
                    is_spam = True
                    break
            job_post.is_spam = is_spam
            job_post.save()

            if not can_post_via_plan and can_post_via_credits:
                request.user.extra_job_posting_credits -= 1
                request.user.save()
                messages.success(request, "İş ilanınız ek ilan kredisi kullanılarak başarıyla yayınlandı!")
            else:
                messages.success(request, "İş ilanınız başarıyla yayınlandı!")
            return redirect('jobs:job_post_list')
    else:
        form = JobPostingForm()
    return render(request, 'jobs/job_post_form.html', {'form': form, 'can_post_via_plan': can_post_via_plan, 'can_post_via_credits': can_post_via_credits})

def job_post_list(request):
    job_posts_query = JobPosting.objects.filter(is_active=True).select_related('employer__user_membership__membership_plan').order_by('-created_at')
    location_q = request.GET.get('location')
    employment_type_q = request.GET.get('employment_type')
    if location_q:
        job_posts_query = job_posts_query.filter(location__icontains=location_q)
    if employment_type_q:
        job_posts_query = job_posts_query.filter(employment_type=employment_type_q)
    locations = JobPosting.objects.filter(is_active=True).values_list('location', flat=True).distinct().order_by('location')
    employment_types = JobPosting.EMPLOYMENT_TYPE_CHOICES
    context = {
        'job_posts': job_posts_query,
        'locations': locations,
        'employment_types': employment_types,
        'selected_location': location_q,
        'selected_employment_type': employment_type_q,
    }
    return render(request, 'jobs/job_post_list.html', context)

from django.contrib.contenttypes.models import ContentType

def job_post_detail(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk)
    # ... (rest of the view) ...
    content_type_id = ContentType.objects.get_for_model(job_post).id
    context = {
        'job_post': job_post,
        'content_type_id': content_type_id,
    }
    return render(request, 'jobs/job_post_detail.html', context)


@login_required
@employer_required
def highlight_job_post(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk, employer=request.user)
    if not job_post.employer == request.user:
        messages.error(request, "Bu ilanı vurgulama yetkiniz yok.")
        return redirect('jobs:job_post_list')
    if job_post.employer.user_membership and job_post.employer.user_membership.is_active and job_post.employer.user_membership.membership_plan.highlight_listings:
        messages.info(request, "Mevcut üyeliğiniz zaten ilan vurgulama özelliğini içeriyor.")
        return redirect('jobs:job_post_detail', pk=pk)
    if request.user.job_highlight_credits > 0:
        messages.success(request, "İlanınız başarıyla vurgulandı!")
        request.user.job_highlight_credits -= 1
        request.user.save()
    else:
        messages.error(request, "İlan vurgulama krediniz bulunmamaktadır. Üyeliğinizi yükselterek veya ürün satın alarak kredi kazanabilirsiniz.")
    return redirect('jobs:job_post_detail', pk=pk)

@login_required
@employer_required
def manage_applications(request):
    applications = Application.objects.filter(job_posting__employer=request.user).select_related('job_posting', 'applicant')
    return render(request, 'jobs/manage_applications.html', {'applications': applications})

@login_required
@employer_required
def update_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk, job_posting__employer=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['approved', 'rejected']:
            application.status = new_status
            application.save()
            Notification.objects.create(
                user=application.applicant,
                message=f"'{application.job_posting.title}' ilanına yaptığınız başvurunun durumu güncellendi: {application.get_status_display()}",
                notification_type='JOB_ALERT',
                related_object_id=application.id
            )
            messages.success(request, f"Başvuru durumu '{application.get_status_display()}' olarak güncellendi.")
        else:
            messages.error(request, "Geçersiz durum.")
    return redirect('jobs:manage_applications')

@login_required
@customer_required
def apply_job(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk)
    if Application.objects.filter(job_posting=job_post, applicant=request.user).exists():
        messages.info(request, "Bu iş ilanına zaten başvurdunuz.")
        return redirect('jobs:job_post_detail', pk=pk)
    if request.method == 'POST':
        application = Application.objects.create(job_posting=job_post, applicant=request.user)
        Notification.objects.create(
            user=job_post.employer,
            message=f"'{job_post.title}' ilanınıza yeni bir başvuru yapıldı.",
            notification_type='JOB_ALERT',
            related_object_id=application.id
        )
        messages.success(request, "İş ilanına başarıyla başvurdunuz!")
        return redirect('user_dashboard')
    return render(request, 'jobs/apply_job.html', {'job_post': job_post})