from django.urls import path
from django.contrib.auth import views as auth_views
from users import views as user_views

urlpatterns = [
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('login/', user_views.MyLoginView.as_view(), name='login'),
    path('logout/', user_views.MyLogoutView.as_view(), name='logout'),
    path('password-reset/', user_views.MyPasswordResetView.as_view(
        template_name='users/password_reset.html'), name='password_reset'),
    path('password-reset/done/', user_views.MyPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', user_views.MyPasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', user_views.MyPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
