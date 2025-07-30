from rest_framework import viewsets, permissions
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer

# I didn't write custom methods like create, retrieve, update, or destroy, because ModelViewSet already includes all of them, wired up to the HTTP methods automatically. DRF maps:

# .list() to GET /api/listings/

# .create() to POST /api/listings/

# .retrieve() to GET /api/listings/{id}/

# .update() to PUT /api/listings/{id}/

# .partial_update() to PATCH /api/listings/{id}/

# .destroy() to DELETE /api/listings/{id}/


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Listings.
    """

    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Bookings.
    """

    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)
