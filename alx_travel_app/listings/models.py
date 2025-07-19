from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Listing(models.Model):
    """
    A place that can be booked.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Booking(models.Model):
    """
    A booking made by a user for a listing.
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(check_out__gt=models.F('check_in')), name='check_out_after_check_in')
        ]

    def __str__(self):
        return f"{self.guest} booked {self.listing} from {self.check_in} to {self.check_out}"


class Review(models.Model):
    """
    A review given by a guest for a listing.
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()  # 1 to 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('listing', 'guest')

    def __str__(self):
        return f"{self.guest} rated {self.listing} {self.rating}/5"
