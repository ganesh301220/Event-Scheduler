from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.shortcuts import get_object_or_404
from requests import request
from .models import Event, EventParticipation
from django.db.models import Count, Q
import razorpay
from django.conf import settings
from .models import Event, EventComment
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from django.utils.timezone import localtime
from .models import EventRating




# ======================================================
# HOME PAGE (PUBLIC)
# ======================================================
def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    context = {
        "upcoming_events": Event.objects
            .filter(status="upcoming")
            .order_by("start_datetime")[:10],
    }

    return render(request, 'home.html', context)




# ======================================================
# USER LOGIN
# ======================================================
def user_login(request):
    if request.method == "POST":
        identifier = request.POST.get("username")  # email OR username
        password = request.POST.get("password")

        # 🔍 Try to get user by email
        try:
            user_obj = User.objects.get(email=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            username = identifier  # fallback to username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid email/username or password")

    return render(request, "login.html")


# ======================================================
# ADMIN LOGIN
# ======================================================
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            login(request, user)
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid admin credentials")

    return render(request, "admin-login.html")


# ======================================================
# ADMIN CHECK
# ======================================================
def is_admin(user):
    return user.is_staff or user.is_superuser


# ======================================================
# ADMIN DASHBOARD + CREATE EVENT
# ======================================================@login_required(login_url="/alogin/")
@user_passes_test(is_admin, login_url="/alogin/")
def admin_dashboard(request):

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        location = request.POST.get("location")
        price_type = request.POST.get("price_type")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        # Combine date + time
        start_datetime = datetime.strptime(
            f"{date} {time}", "%Y-%m-%d %H:%M"
        )
        start_datetime = timezone.make_aware(start_datetime)

        is_paid = True if price_type == "paid" else False
        price = price if is_paid else None

        Event.objects.create(
            title=title,
            description=description,
            start_datetime=start_datetime,
            location=location,
            is_paid=is_paid,
            price=price,
            image=image,
            status="upcoming",
        )

        messages.success(request, "🎉 Event created successfully!")
        return redirect("admin_dashboard")

    context = {
        "total_events": Event.objects.count(),
        "upcoming_events": Event.objects.filter(status="upcoming").count(),
        "ongoing_events": Event.objects.filter(status="ongoing").count(),
        "completed_events": Event.objects.filter(status="completed").count(),
        "total_users": User.objects.count(),
    }

    return render(request, "admin-dashboard.html", context)

@login_required(login_url="/alogin/")
@user_passes_test(is_admin, login_url="/alogin/")
def manage_events(request):
    events = Event.objects.all().order_by("-created_at")
    return render(request, "manage-events.html", {"events": events})


# ==========================
# DELETE EVENT
# ==========================
@login_required(login_url="/alogin/")
@user_passes_test(is_admin)
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, "Event deleted successfully")
    return redirect("manage_events")


# ==========================
# MARK COMPLETED
# ==========================
@login_required(login_url="/alogin/")
@user_passes_test(is_admin)
def mark_completed(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.status = "completed"
    event.save()
    messages.success(request, "Event marked as completed")
    return redirect("manage_events")


# ==========================
# MARK UPCOMING
# ==========================
@login_required(login_url="/alogin/")
@user_passes_test(is_admin)
def mark_upcoming(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.status = "upcoming"
    event.save()
    messages.success(request, "Event marked as upcoming")
    return redirect("manage_events")


@login_required(login_url="/alogin/")
@user_passes_test(is_admin)
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        event.title = request.POST.get("title")
        event.description = request.POST.get("description")
        event.location = request.POST.get("location")
        event.status = request.POST.get("status")

        # ✅ ADD THIS PART (IMAGE UPDATE)
        if request.FILES.get("image"):
            event.image = request.FILES["image"]

        event.save()

        messages.success(request, "Event updated successfully")
        return redirect("manage_events")

    return render(request, "edit-event.html", {"event": event})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user_rating = None

    if request.user.is_authenticated:
        user_rating = EventRating.objects.filter(
            event=event, user=request.user
        ).first()

    context = {
        'event': event,
        'user_rating': user_rating,
    }
    return render(request, 'event-detail.html', context)


@login_required
def rate_event(request, event_id):
    if request.method == "POST":
        rating_value = int(request.POST.get("rating"))
        event = get_object_or_404(Event, id=event_id)

        EventRating.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={'rating': rating_value}
        )

        messages.success(request, "Thanks for rating this event!")
        return redirect('event_detail', event_id=event.id)


@login_required(login_url="login")
def participate_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Prevent duplicate participation
    if EventParticipation.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, "You have already participated in this event.")
        return redirect("event_detail", event_id=event.id)

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        message = request.POST.get("message")

        EventParticipation.objects.create(
            event=event,
            user=request.user,
            name=name,
            email=email,
            mobile=mobile,
            message=message
        )

        messages.success(request, "🎉 You have successfully registered for the event!")
        return redirect("event_detail", event_id=event.id)

    return render(request, "participate.html", {"event": event})
def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Basic validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect("signup")

        # Create user
        user = User.objects.create_user(
            username=email,   # using email as username
            email=email,
            password=password1
        )

        # Save full name
        user.first_name = full_name
        user.save()

        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login")

    return render(request, "signup.html")

def all_events(request):
    filter_type = request.GET.get("type", "all")

    events = Event.objects.all().order_by("-start_datetime")

    if filter_type == "free":
        events = events.filter(is_paid=False)
    elif filter_type == "paid":
        events = events.filter(is_paid=True)

    return render(request, "all-events.html", {
        "events": events,
        "filter_type": filter_type,  # 🔑 for active button
    })

@login_required(login_url="login")
def participate_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Prevent duplicate
    if EventParticipation.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, "You have already participated.")
        return redirect("my_events")

    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        mobile = request.POST["mobile"]
        message = request.POST.get("message", "")

        # -------- FREE EVENT --------
        if not event.is_paid:
            EventParticipation.objects.create(
                user=request.user,
                event=event,
                name=name,
                email=email,
                mobile=mobile,
                message=message
            )
            messages.success(request, "🎉 Registration successful!")
            return redirect("my_events")

        # -------- PAID EVENT --------
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        order = client.order.create({
            "amount": int(event.price * 100),  # paise
            "currency": "INR",
            "payment_capture": 1
        })

        request.session["payment_data"] = {
            "order_id": order["id"],
            "event_id": event.id,
            "name": name,
            "email": email,
            "mobile": mobile,
            "message": message
        }

        return render(request, "razorpay-checkout.html", {
            "order": order,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "event": event
        })

    return render(request, "participate.html", {"event": event})

def contact(request):
    if request.method == "POST":
        messages.success(request, "Your message has been sent successfully!")
    return render(request, "contact.html")

def user_logout(request):
    logout(request)      # ✅ clears session
    return redirect("home")

@login_required
def user_profile(request):
    user = request.user
    return render(request, "user-profile.html", {
        "user_obj": user
    })


@login_required(login_url="login")
def my_events(request):
    participations = (
        EventParticipation.objects
        .filter(user=request.user)
        .select_related("event")
        .order_by("-participated_at")
    )

    return render(request, "my-events.html", {
        "participations": participations
    })

def about(request):
    return render(request, "about.html")

@login_required
@user_passes_test(is_admin)
def view_users(request):
    query = request.GET.get("q", "")

    users = (
        User.objects
        .filter(is_superuser=False)   # 👈 HIDE ADMINS
        .annotate(
            participation_count=Count("event_participations")
        )
        .filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )
        .order_by("-date_joined")
    )

    return render(request, "view-users.html", {
        "users": users,
        "query": query
    })


@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    user.is_active = not user.is_active
    user.save()
    return redirect("view_users")


@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    user.delete()
    return redirect("view_users")


@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id, is_superuser=False)

    participations = (
        Participation.objects
        .filter(user=user)
        .select_related("event")
        .order_by("-joined_at")
    )

    return render(request, "user-detail.html", {
        "user_obj": user,
        "participations": participations
    })

@login_required
def delete_participation(request, participation_id):
    participation = get_object_or_404(
        EventParticipation,
        id=participation_id,
        user=request.user   # 🔐 security: user can delete only own history
    )

    participation.delete()
    messages.success(request, "Participation removed from history.")
    return redirect("my_events")


@login_required
def payment_success(request):
    data = request.session.get("payment_data")

    if not data:
        return redirect("home")

    EventParticipation.objects.create(
        user=request.user,
        event_id=data["event_id"],
        name=data["name"],
        email=data["email"],
        mobile=data["mobile"],
        message=data["message"]
    )

    del request.session["payment_data"]

    messages.success(request, "🎉 Payment successful & registration confirmed!")
    return redirect("my_events")


def all_events(request):
    filter_type = request.GET.get("type", "all")
    search_location = request.GET.get("location", "").strip()

    events = Event.objects.all().order_by("-start_datetime")

    # 🔹 Filter by type
    if filter_type == "free":
        events = events.filter(is_paid=False)
    elif filter_type == "paid":
        events = events.filter(is_paid=True)

    # 🔍 Filter by location (case-insensitive)
    if search_location:
        events = events.filter(location__icontains=search_location)

    return render(request, "all-events.html", {
        "events": events,
        "filter_type": filter_type,
        "search_location": search_location,
    })

@login_required
def event_discussion(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    comments = event.comments.order_by("created_at")

    if request.method == "POST":
        message = request.POST.get("message")
        if message:
            EventComment.objects.create(
                event=event,
                user=request.user,
                message=message,
                is_admin_reply=request.user.is_staff
            )
            return redirect("event_discussion", event_id=event.id)

    return render(request, "event_discussion.html", {
        "event": event,
        "comments": comments
    })

@login_required
def recent_discussions_api(request):
    comments = (
        EventComment.objects
        .select_related("user", "event")
        .order_by("-created_at")[:10]
    )

    data = []
    for c in comments:
        data.append({
            "user": c.user.username,
            "event": c.event.title,
            "message": c.message[:80],
            "event_id": c.event.id,
            "time": c.created_at.strftime("%d %b %H:%M")
        })

    return JsonResponse(data, safe=False)

@login_required
def event_discussion(request, event_id):
    event = Event.objects.get(id=event_id)
    comments = EventComment.objects.filter(event=event).order_by("created_at")

    today = now().date()
    yesterday = today - timedelta(days=1)

    grouped_comments = {
        "today": [],
        "yesterday": [],
        "older": []
    }

    for c in comments:
        if c.created_at.date() == today:
            grouped_comments["today"].append(c)
        elif c.created_at.date() == yesterday:
            grouped_comments["yesterday"].append(c)
        else:
            grouped_comments["older"].append(c)

    if request.method == "POST":
        EventComment.objects.create(
            event=event,
            user=request.user,
            message=request.POST["message"],
            is_admin_reply=request.user.is_staff
        )
        return redirect("event_discussion", event_id=event.id)

    return render(request, "event_discussion.html", {
        "event": event,
        "grouped_comments": grouped_comments
    })
def event_discussion_api(request, event_id):
    event = Event.objects.get(id=event_id)

    comments = EventComment.objects.filter(event=event).order_by("created_at")

    data = []
    for c in comments:
        data.append({
            "user": c.user.username,
            "message": c.message,
            "is_admin": c.is_admin_reply,
            "time": localtime(c.created_at).strftime("%d %b %Y, %I:%M %p"),
            "created_at": c.created_at.isoformat(),
            "event_id": event.id,
        })

    return JsonResponse(data, safe=False)


@login_required
@user_passes_test(is_admin)
def clear_comments_api(request):
    if request.method == "POST":
        EventComment.objects.all().delete()
        return JsonResponse({
            "success": True,
            "message": "All comments deleted"
        })

    return JsonResponse({
        "success": False,
        "error": "Invalid request"
    }, status=400)

@login_required
@user_passes_test(is_admin)
def delete_comment_api(request, id):
    if request.method == "POST":
        try:
            EventComment.objects.get(id=id).delete()
            return JsonResponse({"success": True})
        except EventComment.DoesNotExist:
            return JsonResponse({"success": False}, status=404)


@login_required
@user_passes_test(lambda u: u.is_staff)
def event_participants(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = EventParticipation.objects.filter(event=event)

    return render(request, "event_participants.html", {
        "event": event,
        "participants": participants
    })


@login_required
def remove_participant(request, participant_id):
    participant = get_object_or_404(EventParticipation, id=participant_id)

    # Optional safety check (admin only)
    if not request.user.is_staff:
        messages.error(request, "Unauthorized action.")
        return redirect("/manage-events/")

    participant.delete()
    messages.success(request, "Participant removed successfully.")

    return redirect(request.META.get("HTTP_REFERER", "/manage-events/"))