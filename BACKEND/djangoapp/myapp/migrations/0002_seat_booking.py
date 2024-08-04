# Generated by Django 5.0.7 on 2024-08-03 17:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seat_number', models.CharField(max_length=10)),
                ('is_booked', models.BooleanField(default=False)),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.trainschedule')),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking_date', models.DateTimeField(auto_now_add=True)),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.trainschedule')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('seats', models.ManyToManyField(to='myapp.seat')),
            ],
        ),
    ]
