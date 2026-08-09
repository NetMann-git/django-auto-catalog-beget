# apps/appointments/tests.py

import json
from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.products.models import Product

from .models import Appointment, WorkingHours


class AppointmentModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Тестовое платье",
            slug="test-dress",
            price=100000,
        )

        cls.appointment_date = date(2026, 8, 10)
        cls.appointment_time = time(14, 0)

    def create_appointment(self, **kwargs):
        data = {
            "product": self.product,
            "name": "Тестовый клиент",
            "phone": "+7 (999) 123-45-67",
            "email": "test@example.com",
            "date": self.appointment_date,
            "time": self.appointment_time,
            "status": "pending",
        }
        data.update(kwargs)
        return Appointment.objects.create(**data)

    def test_appointment_can_be_created(self):
        appointment = self.create_appointment()

        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(appointment.status, "pending")

    def test_same_slot_cannot_be_booked_twice(self):
        self.create_appointment()

        with self.assertRaises(ValidationError):
            self.create_appointment()

        self.assertEqual(Appointment.objects.count(), 1)

    def test_cancelled_appointment_does_not_block_slot(self):
        self.create_appointment(status="cancelled")

        appointment = self.create_appointment()

        self.assertEqual(Appointment.objects.count(), 2)
        self.assertEqual(appointment.status, "pending")

    def test_confirmed_appointment_blocks_slot(self):
        self.create_appointment(status="confirmed")

        with self.assertRaises(ValidationError):
            self.create_appointment()

        self.assertEqual(Appointment.objects.count(), 1)


class AvailableSlotsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Тестовое платье",
            slug="test-dress-slots",
            price=100000,
        )

        cls.appointment_date = date(2026, 8, 10)

        WorkingHours.objects.create(
            day_of_week=cls.appointment_date.weekday(),
            start_time=time(10, 0),
            end_time=time(16, 0),
            is_active=True,
        )

    def test_booked_slot_is_not_available(self):
        Appointment.objects.create(
            product=self.product,
            name="Тестовый клиент",
            phone="+7 (999) 123-45-67",
            date=self.appointment_date,
            time=time(14, 0),
            status="pending",
        )

        from .views import get_available_slots

        response = get_available_slots(
            None,
            self.appointment_date.strftime("%Y-%m-%d"),
        )

        data = json.loads(response.content)

        booked_slot = next(
            slot
            for slot in data["slots"]
            if slot["time"] == "14:00"
        )

        self.assertFalse(booked_slot["available"])

    def test_free_slot_is_available(self):
        from .views import get_available_slots

        response = get_available_slots(
            None,
            self.appointment_date.strftime("%Y-%m-%d"),
        )

        data = json.loads(response.content)

        free_slot = next(
            slot
            for slot in data["slots"]
            if slot["time"] == "14:30"
        )

        self.assertTrue(free_slot["available"])