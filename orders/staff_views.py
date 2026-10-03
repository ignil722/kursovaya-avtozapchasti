from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import staff_required

from .forms import OrderStatusForm
from .models import Order
from .services import transition_order


@staff_required
def order_list(request):
    orders = Order.objects.select_related("user").prefetch_related("items")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    if query:
        filters = Q(user__username__icontains=query) | Q(user__email__icontains=query)
        if query.isdigit():
            filters |= Q(pk=int(query))
        orders = orders.filter(filters)
    return render(request, "staff/order_list.html", {"orders": orders, "statuses": Order.Status.choices, "selected_status": status, "query": query})


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("user").prefetch_related("items", "payment_attempts"), pk=pk)
    form = OrderStatusForm(request.POST or None, order=order)
    if request.method == "POST" and form.is_valid():
        try:
            transition_order(order, form.cleaned_data["status"], request.user)
            messages.success(request, "Статус заказа обновлён.")
            return redirect("staff:order_detail", pk=pk)
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
    return render(request, "staff/order_detail.html", {"order": order, "form": form})
