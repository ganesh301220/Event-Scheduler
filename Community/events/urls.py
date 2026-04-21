from django.urls import path
from . import views
from .views import event_detail, view_users, toggle_user_status, delete_user, event_discussion, recent_discussions_api, event_discussion_api
from .views import remove_participant


urlpatterns = [
    # ================= HOME =================
    path("", views.home, name="home"),

    # ================= USER AUTH =================
    path("login/", views.user_login, name="login"),
    path("alogin/", views.admin_login, name="admin_login"),

    # ================= ADMIN DASHBOARD =================
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # ================= EVENT MANAGEMENT =================
    path("manage-events/", views.manage_events, name="manage_events"),
    path("edit-event/<int:event_id>/", views.edit_event, name="edit_event"),
    path("delete-event/<int:event_id>/", views.delete_event, name="delete_event"),
    path("mark-completed/<int:event_id>/", views.mark_completed, name="mark_completed"),
    path("mark-upcoming/<int:event_id>/", views.mark_upcoming, name="mark_upcoming"),

    # ================= EVENT DETAILS =================
path("event/<int:event_id>/rate/", views.rate_event, name="rate_event"),

    path("event/<int:event_id>/", views.event_detail, name="event_detail"),
    path(
        "event/<int:event_id>/participate/",
        views.participate_event,
        name="participate_event",
    ),
        path("my-events/", views.my_events, name="my_events"),
path("admin-users/", view_users, name="view_users"),
    path("toggle-user/<int:user_id>/", toggle_user_status, name="toggle_user"),
    path("delete-user/<int:user_id>/", delete_user, name="delete_user"),
        path("event/<int:event_id>/discussion/", event_discussion, name="event_discussion"),
path("api/recent-discussions/", recent_discussions_api, name="recent_discussions_api"),
path("event/<int:event_id>/discussion/api/", event_discussion_api, name="event_discussion_api"),
    path("api/event/<int:event_id>/discussion/", event_discussion_api, name="event_discussion_api"),
path("api/delete-comment/<int:id>/", views.delete_comment_api, name="delete_comment_api"),
    path("api/clear-comments/", views.clear_comments_api, name="clear_comments_api"),
path("event/<int:event_id>/participants/", views.event_participants, name="event_participants"),

path(
  "remove-participant/<int:participant_id>/",  remove_participant,  name="remove_participant"
)


]
