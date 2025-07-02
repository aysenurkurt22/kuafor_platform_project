from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import JobPosting, Application
from .forms import JobPostingForm
from memberships.models import UserMembership, MembershipPlan
from django.contrib import messages
from datetime import datetime
from users.models import CustomUser

@login_required
def job_post_create(request):
    if not request.user.is_employer:
        messages.error(request, "Sadece işverenler ilan oluşturabilir.")
        return redirect('home')

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
        return redirect('job_post_list')

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_post = form.save(commit=False)
            job_post.employer = request.user
            job_post.save()

            if not can_post_via_plan and can_post_via_credits: # Kredi kullanıldıysa
                request.user.extra_job_posting_credits -= 1
                request.user.save()
                messages.success(request, "İş ilanınız ek ilan kredisi kullanılarak başarıyla yayınlandı!")
            else:
                messages.success(request, "İş ilanınız başarıyla yayınlandı!")
            return redirect('job_post_list')
    else:
        form = JobPostingForm()
    return render(request, 'jobs/job_post_form.html', {'form': form, 'can_post_via_plan': can_post_via_plan, 'can_post_via_credits': can_post_via_credits})

def job_post_list(request):
    job_posts = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'jobs/job_post_list.html', {'job_posts': job_posts})

def job_post_detail(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk)
    # Son görüntülenen iş ilanlarını oturumda sakla
    if 'recently_viewed_jobs' not in request.session:
        request.session['recently_viewed_jobs'] = []
    
    recently_viewed_jobs = request.session['recently_viewed_jobs']
    if job_post.id in recently_viewed_jobs:
        recently_viewed_jobs.remove(job_post.id) # Eğer zaten varsa en üste taşı
    recently_viewed_jobs.insert(0, job_post.id) # En yeni görüntüleneni en başa ekle
    request.session['recently_viewed_jobs'] = recently_viewed_jobs[:5] # Sadece son 5 ilanı sakla
    request.session.modified = True

    # Kullanıcının tercih edilen lokasyonlarını ve yeteneklerini güncelle
    if request.user.is_authenticated:
        user = request.user
        # Lokasyonları güncelle
        current_locations = set(user.preferred_locations.split(',')) if user.preferred_locations else set()
        new_location = job_post.location.strip()
        if new_location and new_location not in current_locations:
            current_locations.add(new_location)
            user.preferred_locations = ', '.join(sorted(list(current_locations)))

        # Yetenekleri güncelle
        current_skills = set(user.preferred_skills.split(',')) if user.preferred_skills else set()
        new_skills = [s.strip() for s in job_post.skills_required.split(',') if s.strip()]
        for skill in new_skills:
            if skill and skill not in current_skills:
                current_skills.add(skill)
        user.preferred_skills = ', '.join(sorted(list(current_skills)))
        user.save()

    return render(request, 'jobs/job_post_detail.html', {'job_post': job_post})

@login_required
def highlight_job_post(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk, employer=request.user)

    if not request.user.is_employer:
        messages.error(request, "Sadece işverenler ilanlarını vurgulayabilir.")
        return redirect('job_post_list')

    if not job_post.employer == request.user:
        messages.error(request, "Bu ilanı vurgulama yetkiniz yok.")
        return redirect('job_post_list')

    if job_post.employer.user_membership and job_post.employer.user_membership.is_active and job_post.employer.user_membership.membership_plan.highlight_listings:
        messages.info(request, "Mevcut üyeliğiniz zaten ilan vurgulama özelliğini içeriyor.")
        return redirect('job_post_detail', pk=pk)

    if request.user.job_highlight_credits > 0:
        # Bu kısım, ilan vurgulama mantığ��nı daha kalıcı hale getirmeli.
        # Şimdilik sadece mesaj gösteriyor ve krediyi düşürüyor.
        # Gerçekte, JobPosting modeline bir 'is_highlighted' veya 'highlight_until' alanı eklenmeli.
        # Ve bu alanın süresi dolduğunda otomatik olarak kaldırılması için bir görev (cron job) ayarlanmalı.
        messages.success(request, "İlanınız başarıyla vurgulandı!")
        request.user.job_highlight_credits -= 1
        request.user.save()
    else:
        messages.error(request, "İlan vurgulama krediniz bulunmamaktadır. Üyeliğinizi yükselterek veya ürün satın alarak kredi kazanabilirsiniz.")
    
    return redirect('job_post_detail', pk=pk)

@login_required
def apply_job(request, pk):
    job_post = get_object_or_404(JobPosting, pk=pk)

    if request.user.is_employer:
        messages.error(request, "İşverenler iş ilanlarına başvuramaz.")
        return redirect('job_post_detail', pk=pk)

    if Application.objects.filter(job_posting=job_post, applicant=request.user).exists():
        messages.info(request, "Bu iş ilanına zaten başvurdunuz.")
        return redirect('job_post_detail', pk=pk)

    if request.method == 'POST':
        # Basit bir başvuru, CV yükleme vb. daha sonra eklenebilir.
        Application.objects.create(job_post_id=job_post.id, applicant=request.user)
        messages.success(request, "İş ilanına başarıyla başvurdunuz!")
        return redirect('user_dashboard') # Başvuru sonrası kontrol paneline yönlendir
    
    return render(request, 'jobs/apply_job.html', {'job_post': job_post}) # Başvuru formu sayfası (şimdilik boş)
