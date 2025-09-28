from django.urls import path
from .views import (
    UserRegisterView,
    UserLoginView,
    UserListView,
    UserUpdateView,
    ChangePasswordView,
)

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('list/', UserListView.as_view(), name='user-list'),
    path('update/', UserUpdateView.as_view(), name='user-update'),
    path('change-password/', ChangePasswordView.as_view(), name='user-change-password'),
] 