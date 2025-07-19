#!/usr/bin/env python3

from rest_framework import serializers
from .models import Listing, Booking


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for Listing model.
    """

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'description',
            'location',
            'price_per_night',
            'host',
            'created_at',
        ]
        read_only_fields = ['id', 'host', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model.
    """

    class Meta:
        model = Booking
        fields = [
            'id',
            'listing',
            'guest',
            'check_in',
            'check_out',
            'created_at',
        ]
        read_only_fields = ['id', 'guest', 'created_at']
