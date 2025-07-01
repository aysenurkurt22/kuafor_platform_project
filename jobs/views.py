from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import JobPosting
from .forms import JobPostingForm
from memberships.models import UserMembership, MembershipPlan
from django.contrib import messages
from datetime import datetime

@login_required
def job_post_create(request):
    if not request.user.is_employer:
        messages.error(request, "Sadece işverenler ilan oluşturabilir.")
        return redirect('home')

    user_membership = UserMembership.objects.filter(user=request.user, is_active=True).first()
    current_month_job_postings = JobPosting.objects.filter(
        employer=request.user,
        created_at__year=datetime.now().year,
        created_at__month=datetime.now().month
    ).count()

    max_postings = 0
    if user_membership:
        max_postings = user_membership.membership_plan.max_job_postings
    elif not user_membership or user_membership.membership_plan.membership_type == 'FREE':
        max_postings = 1 # Free plan limit

    if max_postings != 0 and current_month_job_postings >= max_postings:
        messages.error(request, f"Bu ay için {max_postings} ilan limitinizi doldurdunuz. Üyeliğinizi yükselterek daha fazla ilan yayınlayabilirsiniz.")
        return redirect('job_post_list')

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_post = form.save(commit=False)
            job_post.employer = request.user
            job_post.save()
            messages.success(request, "İş ilanınız başarıyla yayınlandı!")
            return redirect('job_post_list')
    else:
        form = JobPostingForm()
    return render(request, 'jobs/job_post_form.html', {'form': form})

def job_post_list(request):
    job_posts = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'jobs/job_post_list.html', {'job_posts': job_posts})

def job_post_detail(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk)
    return render(request, 'jobs/job_post_detail.html', {'job_post': job_post})