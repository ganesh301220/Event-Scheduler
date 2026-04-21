from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from events.views import delete_participation

# ================= VIEWS =================
from events.views import (
    home,
    signup,
    user_login,
    user_logout,
    admin_login,
    admin_dashboard,
    manage_events,
    edit_event,
    delete_event,
    mark_completed,
    mark_upcoming,
    all_events,
    participate_event,
    contact,
    user_profile,
    about,
    view_users,
    user_detail,
    payment_success,
)

urlpatterns = [

    # ================= DJANGO ADMIN =================
    path("admin/", admin.site.urls),

    # ================= HOME =================
    path("", home, name="home"),

    # ================= USER AUTH =================
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("signup/", signup, name="signup"),

    # ================= ADMIN AUTH =================
    path("alogin/", admin_login, name="admin_login"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),

    # ================= EVENTS =================
    path("events/", all_events, name="all_events"),
    path("event/<int:event_id>/participate/", participate_event, name="participate_event"),

    # ================= EVENT MANAGEMENT (ADMIN) =================
    path("manage-events/", manage_events, name="manage_events"),
    path("edit-event/<int:event_id>/", edit_event, name="edit_event"),
    path("delete-event/<int:event_id>/", delete_event, name="delete_event"),
    path("mark-completed/<int:event_id>/", mark_completed, name="mark_completed"),
    path("mark-upcoming/<int:event_id>/", mark_upcoming, name="mark_upcoming"),

    # ================= USER PAGES =================
    path("profile/", user_profile, name="user_profile"),
    path("contact/", contact, name="contact"),
    path("about/", about, name="about"),

    # ================= ADMIN USERS =================
    path("admin-users/", view_users, name="view_users"),

    # ================= APP URLS (OPTIONAL) =================
    path("", include("events.urls")),
        path("admin-users/<int:user_id>/", user_detail, name="user_detail"),
path(
    "delete-participation/<int:participation_id>/",
    delete_participation,
    name="delete_participation"
),

path("participate/<int:event_id>/", participate_event, name="participate_event"),
path("payment-success/", payment_success, name="payment_success"),


]

# ================= MEDIA FILES =================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
