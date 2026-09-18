# apps/appointments/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from apps.products.models import Product
from apps.users.constants import ROLE_ADMIN, ROLE_MANAGER
from apps.users.decorators import role_required
from .forms import AppointmentForm, CallbackRequestForm
from .notifications import (
    send_email_notification,
    send_telegram_notification,
    send_max_notification,
)

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from datetime import datetime, timedelta
from .models import Appointment, CallbackRequest, WorkingHours


def get_available_slots(request, date):
    """
    Возвращает доступные временные слоты для указанной даты.
    """
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)

    day_of_week = date_obj.weekday()

    try:
        working_hours = WorkingHours.objects.get(
            day_of_week=day_of_week,
            is_active=True,
        )
    except WorkingHours.DoesNotExist:
        return JsonResponse(
            {'error': 'В этот день салон не работает'},
            status=404,
        )

    booked_appointments = set(
        Appointment.objects.filter(
            date=date_obj,
            status__in=['pending', 'confirmed'],
        ).values_list('time', flat=True)
    )

    start = datetime.combine(date_obj, working_hours.start_time)
    end = datetime.combine(date_obj, working_hours.end_time)

    slots = []
    current = start

    while current < end:
        slot_time = current.time()
        time_str = current.strftime('%H:%M')

        slots.append({
            'time': time_str,
            'available': slot_time not in booked_appointments,
        })

        current += timedelta(minutes=30)

    return JsonResponse({
        'date': date,
        'slots': slots,
    })

def appointment_form(request, product_id=None):
    """
    Форма записи на примерку.
    Для AJAX-запросов возвращает только HTML формы без base.html.
    """
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id, is_active=True)

    form = AppointmentForm(initial={'product': product} if product else {})

    context = {
        'form': form,
        'product': product,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'appointments/_appointment_form_ajax.html', context)
    return render(request, 'appointments/appointment_form.html', context)


@require_POST
def appointment_submit(request):
    """
    Обработчик отправки формы записи.
    """
    form = AppointmentForm(request.POST)
    if form.is_valid():
        appointment = form.save()

        try:
            subject = f'Новая запись на примерку — {appointment.name}'
            html_message = render_to_string('appointments/email_admin_notification.html', {
                'appointment': appointment,
                'site_url': settings.SITE_URL,
            })
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f'Ошибка отправки письма администратору: {e}')

        if appointment.email:
            try:
                subject = f'Подтверждение записи на примерку — {appointment.name}'
                html_message = render_to_string('appointments/email_client_confirmation.html', {
                    'appointment': appointment,
                })
                send_mail(
                    subject=subject,
                    message='',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[appointment.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                print(f'Ошибка отправки письма клиенту: {e}')

        messages.success(
            request,
            'Спасибо! Ваша заявка на примерку отправлена. '
            'Мы свяжемся с вами в течение 15 минут для подтверждения.'
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Заявка отправлена'})
        return redirect('catalog:product_detail', slug=appointment.product.slug if appointment.product else 'catalog')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    context = {'form': form}
    return render(request, 'appointments/appointment_form.html', context)

@require_POST
def callback_submit(request):
    """Принимает короткую заявку на обратный звонок с главной страницы."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # Простое honeypot-поле: обычный посетитель его не видит и не заполняет.
    if request.POST.get('website', '').strip():
        message = 'Спасибо! Заявка принята. Мы свяжемся с вами в ближайшее время.'
        if is_ajax:
            return JsonResponse({'success': True, 'message': message})
        messages.success(request, message)
        return redirect(f"{reverse('home')}#callback")

    form = CallbackRequestForm(request.POST)
    if form.is_valid():
        callback = form.save(commit=False)
        callback.source = 'homepage'
        callback.save()

        # Заявка уже сохранена в БД. Ошибка SMTP не влияет на результат формы.
        send_email_notification(callback)
        send_telegram_notification(callback)
        send_max_notification(callback)

        message = 'Спасибо! Заявка принята. Мы свяжемся с вами в ближайшее время.'
        if is_ajax:
            return JsonResponse({'success': True, 'message': message})

        messages.success(request, message)
        return redirect(f"{reverse('home')}#callback")

    errors = {
        field: [str(error) for error in field_errors]
        for field, field_errors in form.errors.items()
    }

    if is_ajax:
        return JsonResponse(
            {
                'success': False,
                'message': 'Проверьте заполнение формы.',
                'errors': errors,
            },
            status=400,
        )

    first_error = next((items[0] for items in errors.values() if items), 'Проверьте заполнение формы.')
    messages.error(request, first_error)
    return redirect(f"{reverse('home')}#callback")

@role_required(ROLE_MANAGER, ROLE_ADMIN)
def callback_request_list(request):
    """Список заявок на обратный звонок для менеджера и администратора."""
    status = request.GET.get("status", "").strip()
    valid_statuses = {value for value, _label in CallbackRequest.STATUS_CHOICES}

    callbacks = CallbackRequest.objects.all()
    if status in valid_statuses:
        callbacks = callbacks.filter(status=status)
    else:
        status = ""

    context = {
        "callbacks": callbacks,
        "status": status,
        "status_choices": CallbackRequest.STATUS_CHOICES,
        "total": CallbackRequest.objects.count(),
        "new_count": CallbackRequest.objects.filter(
            status=CallbackRequest.STATUS_NEW
        ).count(),
    }
    return render(request, "appointments/callback_request_list.html", context)

@require_POST
@role_required(ROLE_MANAGER, ROLE_ADMIN)
def callback_request_status_update(request, pk):
    """Изменяет статус заявки на обратный звонок."""
    callback = get_object_or_404(CallbackRequest, pk=pk)
    status = request.POST.get("status", "").strip()
    valid_statuses = {value for value, _label in CallbackRequest.STATUS_CHOICES}

    if status not in valid_statuses:
        messages.error(request, "Некорректный статус заявки.")
    elif callback.status != status:
        callback.status = status
        callback.save(update_fields=["status", "updated_at"])
        messages.success(request, "Статус заявки изменён.")

    redirect_url = reverse("appointments:callback_request_list")
    current_filter = request.POST.get("current_filter", "").strip()
    if current_filter in valid_statuses:
        redirect_url = f"{redirect_url}?status={current_filter}"

    return redirect(redirect_url)

