import logging
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


logger = logging.getLogger(__name__)


def send_email_notification(callback_request) -> bool:
    """Отправляет менеджеру уведомление о новой заявке на обратный звонок."""
    manager_email = getattr(settings, "MANAGER_EMAIL", "")
    if not manager_email:
        logger.error(
            "Не задан MANAGER_EMAIL: уведомление о заявке #%s не отправлено",
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
            to=[manager_email],
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
        "Email-уведомление о заявке #%s отправлено менеджеру",
        callback_request.pk,
    )
    return True
