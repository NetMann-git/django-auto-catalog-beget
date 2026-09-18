import logging
import re
from html import escape

import requests

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


logger = logging.getLogger(__name__)


def send_email_notification(callback_request) -> bool:
    """Отправляет менеджеру уведомление о новой заявке на обратный звонок."""
    manager_emails = getattr(settings, "MANAGER_EMAILS", [])
    if not manager_emails:
        logger.error(
            "Не задан MANAGER_EMAILS: уведомление о заявке #%s не отправлено",
            callback_request.pk,
        )
        return False

    name = callback_request.name.strip() if callback_request.name else "Без имени"
    phone = callback_request.phone.strip()

    # В текущей модели CallbackRequest комментария пока нет. getattr сохраняет
    # совместимость, если поле comment будет добавлено позже.
    comment = getattr(callback_request, "comment", "") or ""
    comment = comment.strip() or "Не указан"

    created_at = timezone.localtime(callback_request.created_at)
    created_at_text = created_at.strftime("%d.%m.%Y %H:%M")

    subject = f"Новая заявка на обратный звонок от {name}"
    text_body = (
        "Получена новая заявка на обратный звонок.\n\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Комментарий: {comment}\n"
        f"Дата создания: {created_at_text}\n"
    )
    html_body = (
        "<h2>Новая заявка на обратный звонок</h2>"
        f"<p><strong>Имя:</strong> {escape(name)}</p>"
        f"<p><strong>Телефон:</strong> {escape(phone)}</p>"
        f"<p><strong>Комментарий:</strong><br>{escape(comment).replace(chr(10), '<br>')}</p>"
        f"<p><strong>Дата создания:</strong> {escape(created_at_text)}</p>"
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=manager_emails,
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Ошибка отправки email-уведомления о заявке #%s",
            callback_request.pk,
        )
        return False

    logger.info(
        "Email-уведомление о заявке #%s отправлено менеджерам",
        callback_request.pk,
    )
    return True


_MARKDOWN_V2_SPECIAL_CHARS = re.compile(r"([_\*\[\]\(\)~`>#+\-=|{}.!\\])")


def _escape_markdown_v2(value) -> str:
    """Экранирует пользовательский текст для Telegram MarkdownV2."""
    return _MARKDOWN_V2_SPECIAL_CHARS.sub(r"\\\1", str(value or ""))


def send_telegram_notification(callback_request) -> bool:
    """Отправляет менеджеру Telegram-уведомление о новой заявке."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = str(getattr(settings, "TELEGRAM_MANAGER_CHAT_ID", "")).strip()

    if not bot_token or not chat_id:
        logger.warning(
            "Telegram-уведомление о заявке #%s не отправлено: "
            "TELEGRAM_BOT_TOKEN или TELEGRAM_MANAGER_CHAT_ID не настроены",
            callback_request.pk,
        )
        return False

    name = callback_request.name.strip() if callback_request.name else "Без имени"
    phone = callback_request.phone.strip()
    comment = getattr(callback_request, "comment", "") or ""
    comment = comment.strip() or "Не указан"

    text = (
        "📞 *Новая заявка на звонок*\n"
        f"*Имя:* {_escape_markdown_v2(name)}\n"
        f"*Телефон:* {_escape_markdown_v2(phone)}\n"
        f"*Комментарий:* {_escape_markdown_v2(comment)}"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "MarkdownV2",
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception(
            "Ошибка отправки Telegram-уведомления о заявке #%s",
            callback_request.pk,
        )
        return False

    logger.info(
        "Telegram-уведомление о заявке #%s отправлено менеджеру",
        callback_request.pk,
    )
    return True


def send_max_notification(callback_request) -> bool:
    """Отправляет менеджеру MAX-уведомление о новой заявке."""
    bot_token = getattr(settings, "MAX_BOT_TOKEN", "").strip()
    chat_id = str(getattr(settings, "MAX_MANAGER_CHAT_ID", "")).strip()

    if not bot_token or not chat_id:
        logger.warning(
            "MAX-уведомление о заявке #%s не отправлено: "
            "MAX_BOT_TOKEN или MAX_MANAGER_CHAT_ID не настроены",
            callback_request.pk,
        )
        return False

    name = callback_request.name.strip() if callback_request.name else "Без имени"
    phone = callback_request.phone.strip()
    comment = getattr(callback_request, "comment", "") or ""
    comment = comment.strip() or "Не указан"

    text = (
        "📞 *Новая заявка на звонок*\n"
        f"*Имя:* {name}\n"
        f"*Телефон:* {phone}\n"
        f"*Комментарий:* {comment}"
    )

    try:
        response = requests.post(
            "https://platform-api2.max.ru/messages",
            headers={
                "Authorization": bot_token,
                "Content-Type": "application/json",
            },
            params={"chat_id": chat_id},
            json={
                "text": text,
                "format": "markdown",
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception(
            "Ошибка отправки MAX-уведомления о заявке #%s",
            callback_request.pk,
        )
        return False

    logger.info(
        "MAX-уведомление о заявке #%s отправлено менеджеру",
        callback_request.pk,
    )
    return True
