# apps/users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='/'
    ), name='logout'),
    
    # Восстановление пароля
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url='/account/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/account/reset/done/'
         ),
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Продавец
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('consultant/', views.consultant_dashboard, name='consultant_dashboard'),
    path('consultant/calendar/', views.consultant_calendar, name='consultant_calendar'),
    path('appointment/<int:appointment_id>/update-status/', 
         views.appointment_update_status, 
         name='appointment_update_status'),
    
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('appointments/', views.appointments_history, name='appointments'),
    path('favorites/', views.favorites_list, name='favorites'),
    path('reviews/', views.reviews_list, name='reviews'),
    path('consultant/create-appointment/', views.consultant_create_appointment, name='consultant_create_appointment'),

]



