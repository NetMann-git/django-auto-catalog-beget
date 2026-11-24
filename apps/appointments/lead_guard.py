"""Transactional deduplication and rate limits shared by every web worker."""
import ipaddress
import json
import math
import time
from datetime import timedelta

from django.conf import settings
from django.db import OperationalError, connection, transaction
from django.db.models import F
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import CallbackRequest, LeadGuardBucket


class LeadRateLimited(Exception):
    """Tell the caller when the submission can be retried."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__(
            'Слишком много заявок за короткое время. '
            f'Попробуйте через {math.ceil(self.retry_after / 60)} мин.',
        )


def normalized_phone(value: str) -> str:
    """Recognize formatting variants and Russian 8/+7 as one contact."""
    digits = ''.join(ch for ch in value if ch in '0123456789')
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    return digits


def _key(kind: str, value: str) -> str:
    """Do not store IPs or phone numbers in the counter table."""
    return salted_hmac('appointments.lead-guard.' + kind, value,
                       algorithm='sha256').hexdigest()


def _setting(name: str, default: int) -> int:
    """Require positive limits; settings errors must not silently disable them."""
    value = int(getattr(settings, name, default))
    if value < 1:
        raise ValueError(f'{name} must be positive')
    return value


def _ip(request: HttpRequest) -> str:
    """Trust only the address supplied by the web server, never client headers."""
    raw = request.META.get('REMOTE_ADDR', '')
    try:
        address = ipaddress.ip_address(raw)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return str(address)
    except ValueError:
        return 'unknown'


def save_lead(request: HttpRequest, lead: CallbackRequest) -> bool:
    """Retry short SQLite write contention without dropping protection."""
    for attempt in range(5):
        try:
            return _save_lead(request, lead)
        except OperationalError as error:
            if (connection.vendor != 'sqlite' or 'locked' not in str(error).lower()
                    or attempt == 4):
                raise
            time.sleep(0.05 * (attempt + 1))
    raise AssertionError('Unreachable')


@transaction.atomic
def _save_lead(request: HttpRequest, lead: CallbackRequest) -> bool:
    """Save once; return False for a recent duplicate, without notifying again."""
    # UPDATE is the first SQL statement: it obtains a write lock on SQLite and
    # a row lock on InnoDB before reading counters. Network work stays outside.
    if not LeadGuardBucket.objects.filter(key='lock').update(count=F('count')):
        raise RuntimeError('Lead guard lock missing; apply appointments migrations.')
    now = timezone.now()
    phone = normalized_phone(lead.phone)
    payload = json.dumps([
        lead.source, lead.product_id, phone, lead.name.strip(),
        lead.city.strip(), lead.email.strip().casefold(), lead.comment.strip(),
    ], ensure_ascii=False, separators=(',', ':'))
    duplicate_key = _key('duplicate', payload)
    duplicate_seconds = _setting('LEAD_DUPLICATE_SECONDS', 600)
    duplicate = LeadGuardBucket.objects.filter(key=duplicate_key).first()
    if duplicate and duplicate.started_at > now - timedelta(seconds=duplicate_seconds):
        return False

    window = _setting('LEAD_RATE_WINDOW_SECONDS', 900)
    counters = []
    for kind, value, limit in (
        ('phone', phone, _setting('LEAD_PHONE_LIMIT', 5)),
        ('ip', _ip(request), _setting('LEAD_IP_LIMIT', 30)),
    ):
        bucket, _ = LeadGuardBucket.objects.get_or_create(
            key=_key(kind, value), defaults={'started_at': now},
        )
        elapsed = (now - bucket.started_at).total_seconds()
        if elapsed >= window:
            bucket.started_at, bucket.count = now, 0
        if bucket.count >= limit:
            raise LeadRateLimited(math.ceil(window - elapsed))
        counters.append(bucket)

    lead.save()
    for bucket in counters:
        bucket.count += 1
        bucket.save(update_fields=['count', 'started_at'])
    LeadGuardBucket.objects.update_or_create(
        key=duplicate_key, defaults={'started_at': now, 'count': 1},
    )
    # Bounded opportunistic cleanup: no cron required at the default limits.
    retention = max(86400, window, duplicate_seconds)
    expired = list(LeadGuardBucket.objects.exclude(key='lock').filter(
        started_at__lt=now - timedelta(seconds=retention),
    ).values_list('key', flat=True)[:100])
    if expired:
        LeadGuardBucket.objects.filter(key__in=expired).delete()
    return True
