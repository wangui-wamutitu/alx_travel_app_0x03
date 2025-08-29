from rest_framework import viewsets, permissions, status
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
import os
import requests
import uuid
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from .tasks import send_payment_confirmation_email
from .tasks import send_booking_confirmation_email

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
        booking = serializer.save(guest=self.request.user)
        send_booking_confirmation_email.delay(booking.id)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for handling payments with Chapa integration"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter payments by current user"""
        return Payment.objects.filter(booking__user=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate_payment(self, request):
        """Initiate payment with Chapa API"""
        try:
            booking_id = request.data.get('booking_id')
            
            if not booking_id:
                return Response({
                    "error": "booking_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get booking
            try:
                booking = Booking.objects.get(id=booking_id, user=request.user)
            except Booking.DoesNotExist:
                return Response({
                    "error": "Booking not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if payment already exists and is completed
            if hasattr(booking, 'payment') and booking.payment.status == 'completed':
                return Response({
                    "error": "Booking already paid"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate transaction reference
            tx_ref = f"booking_{booking.id}_{uuid.uuid4().hex[:8]}"
            
            # Chapa payload
            chapa_payload = {
                "amount": str(booking.total_price),
                "currency": "ETB",
                "email": request.user.email,
                "first_name": request.user.first_name or "Customer",
                "last_name": request.user.last_name or "User",
                "tx_ref": tx_ref,
                "callback_url": f"{request.build_absolute_uri('/api/payments/callback/')}",
                "return_url": request.data.get('return_url', 'https://yourapp.com/payment/success/'),
                "description": f"Payment for booking {booking.id}"
            }
            
            # Make request to Chapa
            headers = {
                'Authorization': f'Bearer {os.getenv("CHAPA_SECRET_KEY")}',
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                'https://api.chapa.co/v1/transaction/initialize',
                json=chapa_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                chapa_response = response.json()
                
                # Create or update payment record
                payment, created = Payment.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'amount': booking.total_price,
                        'transaction_id': tx_ref,
                        'status': 'pending'
                    }
                )
                
                if not created:
                    payment.transaction_id = tx_ref
                    payment.status = 'pending'
                    payment.save()
                
                return Response({
                    "status": "success",
                    "data": {
                        "payment_id": payment.id,
                        "checkout_url": chapa_response['data']['checkout_url'],
                        "transaction_id": tx_ref,
                        "amount": str(booking.total_price)
                    },
                    "message": "Payment initiated successfully"
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "error": "Payment initiation failed",
                    "details": response.text
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='verify')
    def verify_payment(self, request):
        """Verify payment with Chapa API"""
        try:
            tx_ref = request.data.get('tx_ref')
            
            if not tx_ref:
                return Response({
                    "error": "Transaction reference (tx_ref) is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify with Chapa
            headers = {
                'Authorization': f'Bearer {os.getenv("CHAPA_SECRET_KEY")}',
            }
            
            response = requests.get(
                f'https://api.chapa.co/v1/transaction/verify/{tx_ref}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                verification_data = response.json()
                
                # Get payment record
                try:
                    payment = Payment.objects.get(transaction_id=tx_ref)
                except Payment.DoesNotExist:
                    return Response({
                        "error": "Payment record not found"
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Update payment status based on Chapa response
                if verification_data.get('status') == 'success' and \
                   verification_data.get('data', {}).get('status') == 'success':
                    payment.status = 'completed'
                    payment.booking.status = 'confirmed'
                    payment.booking.save()
                    payment.save()
                    
                    send_payment_confirmation_email.delay(payment.id)
                    
                    serializer = self.get_serializer(payment)
                    return Response({
                        "status": "success",
                        "message": "Payment completed successfully",
                        "data": serializer.data
                    })
                else:
                    payment.status = 'failed'
                    payment.save()
                    
                    return Response({
                        "status": "failed",
                        "message": "Payment verification failed",
                        "reason": verification_data.get('message', 'Unknown error')
                    })
            else:
                return Response({
                    "error": "Payment verification failed",
                    "details": response.text
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "error": f"Verification error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='callback', 
            permission_classes=[AllowAny])
    def payment_callback(self, request):
        """Handle Chapa webhook callback"""
        try:
            tx_ref = request.data.get('tx_ref')
            chapa_status = request.data.get('status')
            
            if not tx_ref:
                return Response({
                    "error": "Transaction reference missing"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                payment = Payment.objects.get(transaction_id=tx_ref)
            except Payment.DoesNotExist:
                return Response({
                    "error": "Payment not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update payment status
            if chapa_status == 'success':
                payment.status = 'completed'
                payment.booking.status = 'confirmed'
                payment.booking.save()
                
                # Send confirmation email
                send_payment_confirmation_email.delay(payment.id)
            else:
                payment.status = 'failed'
            
            payment.save()
            
            return Response({
                "status": "received",
                "message": f"Payment status updated to {payment.status}"
            })
            
        except Exception as e:
            return Response({
                "error": f"Callback error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='status')
    def get_payment_status(self, request, pk=None):
        """Get current payment status"""
        payment = self.get_object()
        serializer = self.get_serializer(payment)
        return Response({
            "status": "success",
            "data": serializer.data
        })
