from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Course, Section, Lesson, Quiz, Question, Answer, Enrollment, UserLessonProgress
from users.decorators import customer_required # Müşteriler için dekoratör
from django.utils.translation import gettext_lazy as _ # Çoklu dil desteği için

def course_list(request):
    courses = Course.objects.filter(is_published=True).order_by('-created_at')
    context = {
        'courses': courses
    }
    return render(request, 'education/course_list.html', context)

def course_detail(request, slug, pk):
    course = get_object_or_404(Course, slug=slug, pk=pk, is_published=True)
    is_enrolled = False
    
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        
        if is_enrolled:
            user_progress_map = {
                progress.lesson.pk: progress.completed
                for progress in UserLessonProgress.objects.filter(user=request.user, lesson__section__course=course)
            }
            
            sections_list = []
            for section in course.sections.all().order_by('order'):
                lessons_list = []
                for lesson in section.lessons.all().order_by('order'):
                    lesson.is_completed_by_user = user_progress_map.get(lesson.pk, False)
                    lessons_list.append(lesson)
                section.lessons_cached = lessons_list
                sections_list.append(section)
            course.sections_cached = sections_list
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'education/course_detail.html', context)

@login_required
@customer_required
def enroll_course(request, slug, pk):
    course = get_object_or_404(Course, slug=slug, pk=pk, is_published=True)
    
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, _("Bu kursa zaten kayıtlısınız."))
        return redirect('education:course_detail', slug=slug, pk=pk)
    
    # if course.price > 0:
    #     messages.warning(request, _("Bu kurs ücretlidir. Ödeme entegrasyonu henüz tamamlanmamıştır."))
    #     return redirect('education:course_detail', slug=slug, pk=pk)

    with transaction.atomic():
        Enrollment.objects.create(user=request.user, course=course)
        messages.success(request, _("Kursa başarıyla kayıt oldunuz!"))
    
    return redirect('education:course_detail', slug=slug, pk=pk)

@login_required
@customer_required
def lesson_detail(request, course_slug, course_pk, lesson_pk):
    course = get_object_or_404(Course, slug=course_slug, pk=course_pk, is_published=True)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, section__course=course)
    
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, _("Bu dersi görüntülemek için kursa kayıtlı olmanız gerekmektedir."))
        return redirect('education:course_detail', slug=course_slug, pk=course_pk)

    user_progress, created = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    context = {
        'course': course,
        'lesson': lesson,
        'user_progress': user_progress,
    }
    return render(request, 'education/lesson_detail.html', context)

@login_required
@customer_required
def mark_lesson_completed(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    user_progress = get_object_or_404(UserLessonProgress, user=request.user, lesson=lesson)
    
    if not user_progress.completed:
        user_progress.completed = True
        user_progress.completion_date = timezone.now()
        user_progress.save()
        messages.success(request, _("Ders başarıyla tamamlandı olarak işaretlendi!"))
    else:
        messages.info(request, _("Bu ders zaten tamamlandı olarak işaretlenmiş."))
    
    return redirect('education:course_detail', slug=lesson.section.course.slug, pk=lesson.section.course.pk)

@login_required
@customer_required
def take_quiz(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk, lesson_type='quiz')
    quiz = get_object_or_404(Quiz, lesson=lesson)
    
    if not Enrollment.objects.filter(user=request.user, course=lesson.section.course).exists():
        messages.error(request, _("Bu quizi çözmek için kursa kayıtlı olmanız gerekmektedir."))
        return redirect('education:course_detail', slug=lesson.section.course.slug, pk=lesson.section.course.pk)

    if request.method == 'POST':
        score = 0
        total_questions = quiz.questions.count()
        for question in quiz.questions.all():
            selected_answer_id = request.POST.get(f'question_{question.pk}')
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(pk=selected_answer_id, question=question)
                    if selected_answer.is_correct:
                        score += 1
                except Answer.DoesNotExist:
                    pass
            
            messages.success(request, _("Quizi tamamladınız! Skorunuz: {score} / {total_questions}").format(score=score, total_questions=total_questions))
            
            user_progress, created = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
            if not user_progress.completed:
                user_progress.completed = True
                user_progress.completion_date = timezone.now()
                user_progress.save()

            return redirect('education:lesson_detail', course_slug=lesson.section.course.slug, course_pk=lesson.section.course.pk, lesson_pk=lesson.pk)
    
    context = {
        'lesson': lesson,
        'quiz': quiz,
    }
    return render(request, 'education/quiz_detail.html', context)
