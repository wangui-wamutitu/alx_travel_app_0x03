#!/usr/bin/env python3

from django.core.management.base import BaseCommand
from listings.models import Listing
from django.contrib.auth import get_user_model
from faker import Faker
import random

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Seed the database with sample listings"

    def handle(self, *args, **options):
        # Create host user if not exists
        host, created = User.objects.get_or_create(username="demo_host")
        if created:
            host.set_password("password123")
            host.save()

        # Clear old data
        Listing.objects.all().delete()

        # Create sample listings
        for _ in range(10):
            Listing.objects.create(
                title=fake.sentence(nb_words=4),
                description=fake.paragraph(nb_sentences=3),
                location=fake.city(),
                price_per_night=random.randint(30, 200),
                host=host,
            )

        self.stdout.write(self.style.SUCCESS("✅ Successfully seeded listings."))
