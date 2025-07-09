from django.urls import path
from . import views

app_name = 'education'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('course/<slug:slug>/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/<slug:slug>/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<slug:course_slug>/<int:course_pk>/lesson/<int:lesson_pk>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_pk>/complete/', views.mark_lesson_completed, name='mark_lesson_completed'),
    path('lesson/<int:lesson_pk>/quiz/', views.take_quiz, name='take_quiz'),
]