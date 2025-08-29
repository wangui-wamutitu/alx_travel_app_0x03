from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment, Booking

@shared_task
def send_payment_confirmation_email(payment_id):
    """Send confirmation email after successful payment"""
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        
        subject = f'Payment Confirmation - Booking #{booking.id}'
        message = f"""
        Dear {booking.user.first_name},
        
        Your payment has been successfully processed!
        
        Booking Details:
        - Booking ID: {booking.id}
        - Amount: ETB {payment.amount}
        - Transaction ID: {payment.transaction_id}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        
        Thank you for your booking!
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False,
        )
        
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")

shared_task
def send_booking_confirmation_email(booking_id: int) -> None:
    """Send booking confirmation email when a new booking is created"""
    try:
        booking = Booking.objects.get(id=booking_id)

        subject = f'Booking Confirmation - Booking #{booking.id}'
        message = f"""
        Dear {booking.user.first_name},

        Your booking has been successfully created!

        Booking Details:
        - Booking ID: {booking.id}
        - Hotel: {booking.hotel.name}
        - Room: {booking.room.room_type}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}

        We look forward to hosting you!
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False,
        )

    except Exception as e:
        print(f"Failed to send booking confirmation email: {e}")
