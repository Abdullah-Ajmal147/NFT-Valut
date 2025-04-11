from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    # path('login/', views.login_view, name='login'), 
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html', next_page='marketplace:home'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='users/logout.html', http_method_names=['get', 'post'] 
    ), name='logout'),

     # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('wallet/', views.wallet, name='wallet'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('claim-commissions/', views.claim_commissions, name='claim_commissions'),

    path('referrals/', views.referrals, name='referrals'),
    path('commissions/', views.commissions, name='commissions'),
    path('ref/<str:referral_code>/', views.register_with_referral, name='register_with_referral'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),

    # Password Change URLs
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='users/password_change.html',
             success_url='/users/password-change/done/'
         ),
         name='password_change'),
    
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ),
         name='password_change_done'),
] 