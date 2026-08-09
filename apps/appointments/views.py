# apps/appointments/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from apps.products.models import Product
from .forms import AppointmentForm

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from datetime import datetime, timedelta
from .models import Appointment, WorkingHours


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