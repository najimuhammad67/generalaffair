"""URL patterns for the users app."""

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardRedirectView.as_view(), name="dashboard"),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path(
        "profile/change-password/",
        views.ChangePasswordView.as_view(),
        name="change_password",
    ),
    # User Management (GA / Manager)
    path("manage/", views.UserListView.as_view(), name="user_list"),
    path("manage/create/", views.UserCreateView.as_view(), name="user_create"),
    path("manage/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    path(
        "manage/<int:pk>/reset-password/",
        views.AdminResetPasswordView.as_view(),
        name="admin_reset_password",
    ),
    path("manage/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
]
