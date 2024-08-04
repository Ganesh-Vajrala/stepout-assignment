from django.db import models
from django.contrib.auth.models import User

class Train(models.Model):
    train_number = models.CharField(max_length=20, unique=True)
    train_name = models.CharField(max_length=100)
    type_of_train = models.CharField(max_length=50)
    starting_point = models.CharField(max_length=100)
    ending_destination = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.train_number} - {self.train_name}"

class TrainSchedule(models.Model):
    train = models.ForeignKey(Train, related_name='schedules', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    seats_available = models.IntegerField()
    date = models.DateField()

    def __str__(self):
        return f"{self.train.train_number} on {self.date}"

class Seat(models.Model):
    schedule = models.ForeignKey(TrainSchedule, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)

class TrainBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.ForeignKey(TrainSchedule, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)
    booking_date = models.DateTimeField(auto_now_add=True)
    booking_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Booking {self.id} by {self.user.username} for {self.schedule}"