from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Train, TrainSchedule, Seat, TrainBooking

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ('id', 'train_number', 'train_name', 'type_of_train', 'starting_point', 'ending_destination')

class TrainScheduleSerializer(serializers.ModelSerializer):
    train = TrainSerializer()
    class Meta:
        model = TrainSchedule
        fields = '__all__'
    
class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    schedule = TrainScheduleSerializer()
    user = serializers.StringRelatedField() 
    seats = SeatSerializer(many=True)
    class Meta:
        model = TrainBooking
        fields = ('id', 'user', 'schedule', 'seats', 'booking_date', 'booking_status')

