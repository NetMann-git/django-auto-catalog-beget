# apps/appointments/tests.py

import json
from datetime import date, time
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from apps.products.models import Product

from .models import Appointment, WorkingHours, CallbackRequest
from .notifications import send_email_notification


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

class CallbackRequestTests(TestCase):
    def test_callback_request_is_saved(self):
        response = self.client.post(
            '/appointments/callback-submit/',
            {'name': 'Иван', 'phone': '+7 (999) 123-45-67'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': 'Спасибо! Заявка принята. Мы свяжемся с вами в ближайшее время.',
        })
        self.assertEqual(CallbackRequest.objects.count(), 1)
        callback = CallbackRequest.objects.get()
        self.assertEqual(callback.name, 'Иван')
        self.assertEqual(callback.phone, '+7 (999) 123-45-67')
        self.assertEqual(callback.source, 'homepage')

    def test_callback_request_rejects_invalid_phone(self):
        response = self.client.post(
            '/appointments/callback-submit/',
            {'name': 'Иван', 'phone': '123'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('phone', response.json()['errors'])
        self.assertEqual(CallbackRequest.objects.count(), 0)

    def test_honeypot_does_not_create_request(self):
        response = self.client.post(
            '/appointments/callback-submit/',
            {'name': 'Bot', 'phone': '+79991234567', 'website': 'https://spam.example'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(CallbackRequest.objects.count(), 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="site@example.com",
    MANAGER_EMAILS=["manager1@example.com", "manager2@example.com"],
)
class CallbackEmailNotificationTests(TestCase):
    def test_send_email_notification(self):
        callback = CallbackRequest.objects.create(
            name="Иван",
            phone="+7 (999) 123-45-67",
        )

        result = send_email_notification(callback)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            "Новая заявка на обратный звонок от Иван",
        )
        self.assertEqual(
            message.to,
            ["manager1@example.com", "manager2@example.com"],
        )
        self.assertEqual(message.from_email, "site@example.com")
        self.assertIn("Имя: Иван", message.body)
        self.assertIn("Телефон: +7 (999) 123-45-67", message.body)
        self.assertIn("Комментарий: Не указан", message.body)
        self.assertEqual(len(message.alternatives), 1)
        self.assertEqual(message.alternatives[0].mimetype, "text/html")

    @patch(
        "apps.appointments.notifications.EmailMultiAlternatives.send",
        side_effect=ConnectionError("SMTP unavailable"),
    )
    def test_email_error_does_not_raise_and_request_stays_in_db(self, mocked_send):
        callback = CallbackRequest.objects.create(
            name="Иван",
            phone="+7 (999) 123-45-67",
        )

        result = send_email_notification(callback)

        self.assertFalse(result)
        self.assertTrue(CallbackRequest.objects.filter(pk=callback.pk).exists())
