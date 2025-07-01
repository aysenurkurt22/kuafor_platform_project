from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Lesson, Enrollment

def course_list(request):
    courses = Course.objects.all().order_by('title')
    return render(request, 'education/course_list.html', {'courses': courses})

def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    lessons = course.lessons.all()
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    return render(request, 'education/course_detail.html', {'course': course, 'lessons': lessons, 'is_enrolled': is_enrolled})

@login_required
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'Bu kursa zaten kayıtlısınız.')
        return redirect('course_detail', pk=pk)
    
    # Eğer kurs ücretliyse, ödeme entegrasyonu burada olacak (şimdilik yer tutucu)
    # Varsayalım ki ödeme başarılı
    Enrollment.objects.create(user=request.user, course=course)
    messages.success(request, f'{course.title} kursuna başarıyla kayıt oldunuz!')
    return redirect('course_detail', pk=pk)

@login_required
def lesson_detail(request, course_pk, lesson_pk):
    course = get_object_or_404(Course, pk=course_pk)
    lesson = get_object_or_404(Lesson, pk=lesson_pk, course=course)
    
    # Kullanıcının kursa kayıtlı olup olmadığını kontrol et
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, 'Bu dersi görüntülemek için önce kursa kayıt olmalısınız.')
        return redirect('course_detail', pk=course_pk)

    return render(request, 'education/lesson_detail.html', {'course': course, 'lesson': lesson})