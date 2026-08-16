from django.test import TestCase, RequestFactory

from apps.products.session_service import SessionService
from django.contrib.sessions.backends.db import SessionStore


class SessionServiceRecentlyViewedTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        # RequestFactory сам по себе не создаёт полноценную session,
        # поэтому используем простую session-подобную структуру.
        self.request.session = SessionStore()

    def test_get_recently_viewed_returns_empty_list(self):
        result = SessionService.get_recently_viewed(self.request)

        self.assertEqual(result, [])

    def test_save_recently_viewed_adds_product_to_beginning(self):
        SessionService.save_recently_viewed(
            self.request,
            product_id=10,
            limit=5,
        )

        self.assertEqual(
            SessionService.get_recently_viewed(self.request),
            [10],
        )

    def test_save_recently_viewed_puts_new_product_first(self):
        SessionService.save_recently_viewed(
            self.request,
            product_id=10,
            limit=5,
        )

        SessionService.save_recently_viewed(
            self.request,
            product_id=20,
            limit=5,
        )

        self.assertEqual(
            SessionService.get_recently_viewed(self.request),
            [20, 10],
        )

    def test_save_recently_viewed_moves_existing_product_to_first(self):
        SessionService.save_recently_viewed(
            self.request,
            product_id=10,
            limit=5,
        )

        SessionService.save_recently_viewed(
            self.request,
            product_id=20,
            limit=5,
        )

        SessionService.save_recently_viewed(
            self.request,
            product_id=10,
            limit=5,
        )

        self.assertEqual(
            SessionService.get_recently_viewed(self.request),
            [10, 20],
        )

    def test_save_recently_viewed_respects_limit(self):
        for product_id in range(1, 6):
            SessionService.save_recently_viewed(
                self.request,
                product_id=product_id,
                limit=3,
            )

        self.assertEqual(
            SessionService.get_recently_viewed(self.request),
            [5, 4, 3],
        )


class SessionServiceComparisonTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        self.request.session = SessionStore()

    def test_get_comparison_returns_empty_list(self):
        result = SessionService.get_comparison(self.request)

        self.assertEqual(result, [])

    def test_add_to_comparison(self):
        result = SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        self.assertEqual(result, [10])

    def test_add_to_comparison_does_not_create_duplicates(self):
        SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        result = SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        self.assertEqual(result, [10])

    def test_remove_from_comparison(self):
        SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        SessionService.add_to_comparison(
            self.request,
            product_id=20,
        )

        result = SessionService.remove_from_comparison(
            self.request,
            product_id=10,
        )

        self.assertEqual(result, [20])

    def test_remove_missing_product_does_nothing(self):
        SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        result = SessionService.remove_from_comparison(
            self.request,
            product_id=999,
        )

        self.assertEqual(result, [10])

    def test_can_add_to_comparison_when_below_limit(self):
        SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        self.assertTrue(
            SessionService.can_add_to_comparison(
                self.request,
                limit=2,
            )
        )

    def test_cannot_add_to_comparison_when_limit_reached(self):
        SessionService.add_to_comparison(
            self.request,
            product_id=10,
        )

        SessionService.add_to_comparison(
            self.request,
            product_id=20,
        )

        self.assertFalse(
            SessionService.can_add_to_comparison(
                self.request,
                limit=2,
            )
        )