# ALX Travel App

A simple Django-based backend for managing travel-related listings, bookings, and reviews.

## Features

- MySQL-backed database for persistence
- Models:
  - `Listing`: Represents a travel destination or accommodation
  - `Booking`: Connects users with listings and captures booking details
  - `Review`: Allows users to rate and review listings
- Admin interface for managing data
- Seeder script to populate the database with sample listings
- Environment-based configuration with `django-environ`

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo_url>
cd alx_travel_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
