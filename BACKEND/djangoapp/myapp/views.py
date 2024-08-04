from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import Train, TrainSchedule, Seat, TrainBooking
from .serializers import RegisterSerializer, TrainSerializer, TrainScheduleSerializer, SeatSerializer, BookingSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views import View
from django.contrib.auth import authenticate
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db.models import Count
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class TrainCreateView(generics.CreateAPIView):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer
    permission_classes = (AllowAny,)

class TrainScheduleCreateView(generics.CreateAPIView):
    queryset = TrainSchedule.objects.all()
    serializer_class = TrainScheduleSerializer
    permission_classes = (AllowAny,)

@api_view(['POST'])
def create_schedule(request):
    serializer = TrainScheduleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_trains(request):
    source = request.query_params.get('source')
    destination = request.query_params.get('destination')
    date = request.query_params.get('date')

    if not source or not destination or not date:
        return Response({"error": "source, destination, and date are required parameters"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        date_obj = timezone.datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch trains that match the source and destination
    trains = Train.objects.filter(starting_point=source, ending_destination=destination)
    if not trains.exists():
        return Response({"message": "No trains available for the selected route and date"}, status=status.HTTP_404_NOT_FOUND)

    # Fetch schedules for these trains on the specified date
    train_schedules = TrainSchedule.objects.filter(train__in=trains, date=date_obj)

    if not train_schedules.exists():
        return Response({"message": "No trains available for the selected route and date"}, status=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    results = []

    for schedule in train_schedules:
        # Calculate total seats and booked seats
        total_seats = Seat.objects.filter(schedule=schedule).count()
        booked_seats = Seat.objects.filter(schedule=schedule, is_booked=True).count()
        vacant_seats = total_seats - booked_seats

        # Determine if the schedule should be blocked
        start_time = schedule.start_time
        is_blocked = False
        if (start_time - now) <= timedelta(minutes=30):
            is_blocked = True
        elif vacant_seats <= 0:
            is_blocked = True

        # Serialize the schedule
        schedule_data = TrainScheduleSerializer(schedule).data
        schedule_data['total_seats'] = total_seats
        schedule_data['vacant_seats'] = vacant_seats
        schedule_data['is_blocked'] = is_blocked

        # Add train information
        train = schedule.train
        schedule_data['train_name'] = train.train_name
        schedule_data['type_of_train'] = train.type_of_train
        schedule_data['train_number'] = train.train_number

        results.append(schedule_data)

    return Response(results, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_schedule_id(request):
    train_number = request.data.get('train_number')
    date = request.data.get('date')
    
    if not all([train_number, date]):
        return Response({"error": "Train number and date are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find the train by number
        train = Train.objects.get(train_number=train_number)
        
        # Find the schedule for the given date
        schedule = TrainSchedule.objects.get(train=train, date=date)
        
        return Response({"schedule_id": schedule.id}, status=status.HTTP_200_OK)
    except Train.DoesNotExist:
        return Response({"error": "Train not found"}, status=status.HTTP_404_NOT_FOUND)
    except TrainSchedule.DoesNotExist:
        return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_seats_by_schedule(request):
    data = request.data
    schedule_id = data.get('schedule_id')
    print('Received schedule_id:', schedule_id)

    if not schedule_id:
        return Response({"detail": "schedule_id field is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Ensure schedule_id is an integer
        schedule_id = int(schedule_id)
        
        # Fetch seats for the given schedule_id
        seats = Seat.objects.filter(schedule_id=schedule_id)
        print('Fetched seats:', seats)

        if not seats.exists():
            return Response({"detail": "No seats found for this schedule"}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize and return seat data
        serializer = SeatSerializer(seats, many=True)
        return Response(serializer.data)
    
    except ValueError:
        return Response({"detail": "Invalid schedule_id format. Must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Log the unexpected error
        print(f"Unexpected error: {e}")
        return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    data = request.data
    user = request.user
    
    # Extract data from request
    schedule_id = data.get('schedule_id')
    seat_ids = data.get('seat_ids')  # Expecting a list of seat IDs

    if not schedule_id or not seat_ids:
        return Response({"detail": "schedule_id and seat_ids fields are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Convert schedule_id to integer
        schedule_id = int(schedule_id)
        
        # Fetch the train schedule
        schedule = TrainSchedule.objects.get(id=schedule_id)
        
        # Fetch seats based on provided seat IDs
        seats = Seat.objects.filter(id__in=seat_ids, schedule_id=schedule_id)
        
        if seats.count() != len(seat_ids):
            return Response({"detail": "Some seats are not available for this schedule."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if any of the seats are already booked
        if seats.filter(is_booked=True).exists():
            return Response({"detail": "Some of the selected seats are already booked."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark seats as booked
        seats.update(is_booked=True)
        
        # Determine booking status
        booking_status = 'CONFIRMED' if seats.count() == len(seat_ids) else 'PENDING'
        
        # Create booking
        booking = TrainBooking.objects.create(user=user, schedule=schedule, booking_status=booking_status)
        booking.seats.set(seats)  # Associate selected seats with the booking
        booking.save()
        
        # Serialize and return booking data
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except TrainSchedule.DoesNotExist:
        return Response({"detail": "Train schedule not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"detail": "Invalid schedule_id format. Must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomAuthToken(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user is None:
            if not User.objects.filter(username=username).exists():
                return Response({'error': 'Username does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)
        
        token, created = Token.objects.get_or_create(user=user)
        return Response( {
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_superuser,
            'token': token.key,
        })
    
class TrainScheduleListView(View):
    def get(self, request, train_id):
        try:
            schedules = TrainSchedule.objects.filter(train_id=train_id)
            data = [
                {
                    'start_time': schedule.start_time,
                    'end_time': schedule.end_time,
                    'seats_available': schedule.seats_available,
                    'date': schedule.date,
                }
                for schedule in schedules
            ]
            return JsonResponse(data, safe=False, status=200)
        except TrainSchedule.DoesNotExist:
            return JsonResponse({'error': 'Train schedules not found'}, status=404)
    
def check_train_exists(request, train_number):
    try:
        # Try to get the train with the given train number
        train = Train.objects.get(train_number=train_number)
        # If found, return the train details
        data = {
            'id': train.id,
            'train_number': train.train_number,
            'train_name': train.train_name,
            'type_of_train': train.type_of_train,
            'starting_point': train.starting_point,
            'ending_destination': train.ending_destination,
        }
        return JsonResponse(data, status=200)
    except Train.DoesNotExist:
        # If not found, return a 404 status
        return JsonResponse({'message': 'Train does not exist'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_reservations(request):
    user = request.user
    reservations = TrainBooking.objects.filter(user=user).select_related('schedule__train')
    
    if not reservations.exists():
        return Response({"message": "No reservations found."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = BookingSerializer(reservations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
