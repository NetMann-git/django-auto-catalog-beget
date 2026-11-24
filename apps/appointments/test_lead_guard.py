"""Exercise public forms without sending messages to real recipients."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.db import IntegrityError, close_old_connections
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.products.models import Product
from .forms import CallbackRequestForm, CarInquiryForm
from .lead_guard import save_lead
from .models import CallbackRequest, LeadGuardBucket


class LeadGuardTests(TestCase):
    def setUp(self):
        self.callbacks = reverse('appointments:callback_submit')
        self.product = Product.objects.create(title='Авто', slug='auto', price=1)
        self.inquiry = reverse('appointments:car_inquiry', args=[self.product.pk])
        self.data = {'name': 'Иван', 'phone': '+7 (999) 123-45-67', 'city': 'Ростов'}
        self.notifications = []
        for name in ('send_email_notification', 'send_telegram_notification', 'send_max_notification'):
            patcher = patch('apps.appointments.views.' + name, return_value=True)
            self.notifications.append(patcher.start())
            self.addCleanup(patcher.stop)

    def post(self, url=None, data=None, ip='198.51.100.1', **kwargs):
        return self.client.post(
            url or self.callbacks, data or self.data, REMOTE_ADDR=ip,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest', **kwargs,
        )

    def test_duplicate_callback_has_one_record_and_notification(self):
        for _ in range(2):
            self.assertEqual(self.post().status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 1)
        for notify in self.notifications:
            self.assertEqual(notify.call_count, 1)

    def test_duplicate_inquiry_and_order_keep_separate_intent(self):
        for url in (self.inquiry, self.inquiry + '?type=order'):
            for _ in range(2):
                self.assertTrue(self.post(url).json()['success'])
        self.assertEqual(CallbackRequest.objects.count(), 2)
        for notify in self.notifications:
            self.assertEqual(notify.call_count, 2)

    def test_phone_formats_and_different_ip_do_not_bypass_duplicate(self):
        self.post()
        self.post(data={**self.data, 'phone': '8 999 123 45 67'}, ip='198.51.100.2')
        self.assertEqual(CallbackRequest.objects.count(), 1)

    @override_settings(LEAD_PHONE_LIMIT=2)
    def test_phone_limit_shared_between_forms_and_ips(self):
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.post(self.inquiry, ip='198.51.100.2').status_code, 200)
        result = self.post(self.inquiry + '?type=order', ip='198.51.100.3')
        self.assertEqual(result.status_code, 429)
        self.assertIn('Retry-After', result)
        self.assertContains(result, 'Слишком много заявок', status_code=429)
        self.assertEqual(CallbackRequest.objects.count(), 2)

    @override_settings(LEAD_IP_LIMIT=2)
    def test_ip_limit_cannot_be_bypassed_by_forwarded_header(self):
        for i in range(2):
            self.assertEqual(self.post(data={**self.data, 'phone': f'+7999123456{i}'}).status_code, 200)
        result = self.post(
            data={**self.data, 'phone': '+79991234569'},
            HTTP_X_FORWARDED_FOR='203.0.113.77',
        )
        self.assertEqual(result.status_code, 429)
        self.assertFalse(result.json()['success'])
        self.assertEqual(CallbackRequest.objects.count(), 2)

    @override_settings(LEAD_PHONE_LIMIT=1)
    def test_duplicate_is_still_success_at_limit(self):
        self.post()
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 1)

    @override_settings(LEAD_PHONE_LIMIT=1)
    def test_expired_counters_allow_new_submission(self):
        self.post()
        LeadGuardBucket.objects.exclude(key='lock').update(
            started_at=timezone.now() - timedelta(hours=1),
        )
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 2)

    def test_honeypot_creates_no_records_and_sends_nothing(self):
        for url in (self.callbacks, self.inquiry, self.inquiry + '?type=order'):
            self.assertEqual(self.post(url, {**self.data, 'website': 'spam'}).status_code, 200)
        self.assertFalse(CallbackRequest.objects.exists())
        self.assertEqual(LeadGuardBucket.objects.count(), 1)
        for notify in self.notifications:
            notify.assert_not_called()

    def test_invalid_fields_do_not_consume_quota(self):
        for phone in ('abc79991234567', '٧٩٩٩١٢٣٤٥٦٧', '123'):
            self.assertEqual(self.post(data={**self.data, 'phone': phone}).status_code, 400)
        self.assertEqual(LeadGuardBucket.objects.count(), 1)
        self.assertFalse(CallbackRequest.objects.exists())
        form = CarInquiryForm({**self.data, 'comment': 'a' * 2001})
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)

    def test_csrf_remains_required(self):
        client = Client(enforce_csrf_checks=True)
        for url in (self.callbacks, self.inquiry):
            self.assertEqual(client.post(url, self.data).status_code, 403)
        self.assertFalse(CallbackRequest.objects.exists())

    @override_settings(LEAD_PHONE_LIMIT=1)
    def test_non_ajax_preserves_feedback_and_order_confirmation(self):
        first = self.client.post(self.inquiry + '?type=order', self.data)
        second = self.client.post(self.inquiry + '?type=order', self.data)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(self.client.session['car_order_success_product_id'], self.product.pk)
        response = self.client.post(self.inquiry, self.data)
        self.assertContains(response, 'Слишком много заявок', status_code=429)

    def test_rollback_does_not_mark_unsaved_lead_as_duplicate(self):
        request = RequestFactory().post('/', REMOTE_ADDR='198.51.100.1')
        form = CallbackRequestForm(self.data)
        self.assertTrue(form.is_valid())
        lead = form.save(commit=False)
        with patch.object(CallbackRequest, 'save', side_effect=IntegrityError('test')):
            with self.assertRaises(IntegrityError):
                save_lead(request, lead)
        self.assertEqual(LeadGuardBucket.objects.count(), 1)
        self.assertTrue(save_lead(request, lead))
        self.assertEqual(CallbackRequest.objects.count(), 1)

    def test_guard_keys_contain_no_plain_contacts(self):
        self.post()
        for key in LeadGuardBucket.objects.exclude(key='lock').values_list('key', flat=True):
            self.assertEqual(len(key), 64)
            self.assertNotIn('79991234567', key)
            self.assertNotIn('198.51.100.1', key)


class ConcurrentLeadTests(TransactionTestCase):
    def test_simultaneous_identical_submissions_save_once(self):
        LeadGuardBucket.objects.get_or_create(
            key='lock', defaults={'started_at': timezone.now(), 'count': 0},
        )
        barrier = Barrier(2)

        def submit():
            close_old_connections()
            try:
                request = RequestFactory().post('/', REMOTE_ADDR='198.51.100.1')
                lead = CallbackRequest(name='Иван', phone='+79991234567')
                barrier.wait(timeout=5)
                return save_lead(request, lead)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: submit(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(CallbackRequest.objects.count(), 1)
