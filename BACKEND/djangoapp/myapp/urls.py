from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import RegisterView, check_train_exists, TrainScheduleListView, TrainCreateView, TrainScheduleCreateView, CustomAuthToken, get_user_reservations, search_trains, get_seats_by_schedule,create_booking, get_schedule_id

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('api/create-train/', TrainCreateView.as_view(), name ="create-train"),
    path('api/train/<str:train_number>/', check_train_exists, name='check_train_exists'),
    path('api/schedule/', TrainScheduleCreateView.as_view(), name='add_schedule'),
    path('api/search-trains/', search_trains, name='search_trains'),
    path('api/get-schedule-id/', get_schedule_id, name='get_schedule_id'),
    path('api/available_seats/', get_seats_by_schedule, name='get_seats_by_schedule'),
    path('api/create-booking/', create_booking, name='create-booking'),
    path('api/my-reservations/', get_user_reservations, name='my_reservations'),
    path('api/schedules/<int:train_id>/', TrainScheduleListView.as_view(), name='train_schedules'),


]
