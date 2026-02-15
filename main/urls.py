from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('test/create/', views.create_test, name='create_test'),
    path('test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('test/<int:test_id>/submit/', views.submit_answers, name='submit_answers'),
    path('test/<int:test_id>/result/', views.test_result, name='test_result'),
    path('test/code/', views.enter_test_code, name='enter_test_code'),
    path('test/created/<str:test_code>/', views.test_created, name='test_created'),
    path('test/<int:test_id>/', views.test_detail, name='test_detail'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('test/<int:test_id>/toggle_active/', views.toggle_test_active, name='toggle_test_active'),
    path('test/<int:test_id>/results/', views.test_results, name='test_results'),
    path('generate-custom-test/', views.generate_custom_test, name='generate_custom_test'),
]