from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.users.constants import ROLE_ADMIN, ROLE_MANAGER
from apps.users.decorators import role_required

from .forms import ClientShowcaseForm
from .models import ClientShowcase


@role_required(ROLE_MANAGER, ROLE_ADMIN)
def client_list_manage(request):
    clients = ClientShowcase.objects.all()

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        clients = clients.filter(Q(name__icontains=search) | Q(vehicle__icontains=search))

    if status == "published":
        clients = clients.filter(is_published=True)
    elif status == "hidden":
        clients = clients.filter(is_published=False)

    total = clients.count()
    page_obj = Paginator(clients, 24).get_page(request.GET.get("page"))

    return render(
        request,
        "home/manage/clients_list.html",
        {
            "clients": page_obj,
            "total": total,
            "search": search,
            "status": status,
        },
    )


@role_required(ROLE_MANAGER, ROLE_ADMIN)
def client_create(request):
    if request.method == "POST":
        form = ClientShowcaseForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Клиент «{client.name}» создан.')
            return redirect("home:client_list_manage")
    else:
        next_order = (ClientShowcase.objects.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0) + 10
        form = ClientShowcaseForm(initial={"sort_order": next_order, "is_published": True})

    return render(request, "home/manage/client_form.html", {"form": form, "title": "Добавить клиента"})


@role_required(ROLE_MANAGER, ROLE_ADMIN)
def client_edit(request, client_id):
    client = get_object_or_404(ClientShowcase, pk=client_id)

    if request.method == "POST":
        form = ClientShowcaseForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Карточка «{client.name}» обновлена.')
            return redirect("home:client_list_manage")
    else:
        form = ClientShowcaseForm(instance=client)

    return render(
        request,
        "home/manage/client_form.html",
        {"form": form, "client": client, "title": "Редактировать клиента"},
    )


@require_POST
@role_required(ROLE_MANAGER, ROLE_ADMIN)
def client_toggle_published(request, client_id):
    client = get_object_or_404(ClientShowcase, pk=client_id)
    client.is_published = not client.is_published
    client.save(update_fields=("is_published", "updated_at"))

    state = "опубликован" if client.is_published else "снят с публикации"
    messages.success(request, f'Клиент «{client.name}» {state}.')
    return redirect(request.POST.get("next") or "home:client_list_manage")
