from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    """
    Stores community event details
    """

    STATUS_CHOICES = (
        ("upcoming", "Upcoming"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
    )

    # ================= BASIC INFO =================
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)

    # ================= DATE & TIME =================
    start_datetime = models.DateTimeField()

    # ================= PRICING =================
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ================= DISCOUNT =================
    discount_percent = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Enter discount percentage if any"
    )

    # ================= MEDIA =================
    image = models.ImageField(
        upload_to="events/",
        null=True,
        blank=True
    )

    # ================= STATUS =================
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="upcoming"
    )

    # ================= META =================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_datetime"]

    def discounted_price(self):
        """
        Returns discounted price if discount exists,
        otherwise returns original price.
        """
        if self.is_paid and self.discount_percent:
            return self.price - (self.price * self.discount_percent / 100)
        return self.price

    def average_rating(self):
        """
        Returns average rating for the event
        """
        ratings = self.ratings.all()
        if ratings.count() == 0:
            return 0
        return round(sum(r.rating for r in ratings) / ratings.count(), 1)

    def __str__(self):
        return self.title


class EventParticipation(models.Model):
    """ Stores which user participated in which event"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_participations"
    )

    # ================= USER DETAILS =================
    name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    message = models.TextField(blank=True)

    # ================= META =================
    participated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["-participated_at"]
        verbose_name = "Event Participation"
        verbose_name_plural = "Event Participations"

    def __str__(self):
        return f"{self.user.username} → {self.event.title}"


class EventComment(models.Model):
    """
    Stores comments & admin replies for events
    """

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField()
    is_admin_reply = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"


class EventRating(models.Model):
    """
    Stores user ratings for events (1–5 stars)
    """

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_ratings"
    )
    rating = models.PositiveSmallIntegerField()

    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["-rated_at"]
        verbose_name = "Event Rating"
        verbose_name_plural = "Event Ratings"

    def __str__(self):
        return f"{self.user.username} rated {self.rating}⭐ for {self.event.title}"
