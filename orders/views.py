from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from catalog.models import Product

from .forms import CheckoutForm, PaymentForm
from .models import CartItem, Order
from .services import StockError, add_to_cart, cancel_order, create_order, get_cart, process_payment


@login_required
def cart_view(request):
    if request.user.is_store_admin:
        return redirect("staff:order_list")
    cart = get_cart(request.user)
    items = cart.items.select_related("product__manufacturer", "product__category")
    return render(request, "orders/cart.html", {"cart": cart, "items": items})


@login_required
def cart_add(request, product_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.user.is_store_admin:
        messages.info(request, "Корзина доступна покупателям. Администратор управляет каталогом и заказами.")
        return redirect("staff:product_list")
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        add_to_cart(request.user, product, 1)
        messages.success(request, "Товар добавлен в корзину.")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect(product.get_absolute_url())


@login_required
def cart_update(request, item_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.user.is_store_admin:
        return redirect("staff:order_list")
    item = get_object_or_404(CartItem.objects.select_related("product"), pk=item_id, cart__user=request.user)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    if quantity <= 0:
        item.delete()
        messages.info(request, "Товар удалён из корзины.")
    elif quantity > item.product.stock:
        messages.error(request, f"Доступно только {item.product.stock} шт.")
    else:
        item.quantity = quantity
        item.full_clean()
        item.save(update_fields=("quantity",))
    return redirect("orders:cart")


@login_required
def cart_remove(request, item_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.user.is_store_admin:
        return redirect("staff:order_list")
    get_object_or_404(CartItem, pk=item_id, cart__user=request.user).delete()
    messages.info(request, "Товар удалён из корзины.")
    return redirect("orders:cart")


@login_required
def checkout(request):
    if request.user.is_store_admin:
        return redirect("staff:order_list")
    cart = get_cart(request.user)
    if not cart.items.exists():
        messages.info(request, "Сначала добавьте товары в корзину.")
        return redirect("catalog:list")
    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            order = create_order(request.user, form.cleaned_data["delivery_address"])
            return redirect("orders:payment", pk=order.pk)
        except StockError as exc:
            messages.error(request, exc.messages[0])
            return redirect("orders:cart")
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
    return render(request, "orders/checkout.html", {"form": form, "cart": cart, "items": cart.items.select_related("product")})


@login_required
def payment(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk, user=request.user)
    if order.status != Order.Status.CREATED:
        return redirect("orders:detail", pk=order.pk)
    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        attempt = process_payment(order, form.cleaned_data["card_number"])
        if attempt.status == attempt.Status.SUCCESS:
            messages.success(request, "Тестовая оплата прошла успешно.")
            return redirect("orders:detail", pk=order.pk)
        messages.error(request, "Банк отклонил тестовую операцию. Попробуйте карту 4242 4242 4242 4242.")
    return render(request, "orders/payment.html", {"form": form, "order": order})


@login_required
def order_history(request):
    if request.user.is_store_admin:
        return redirect("staff:order_list")
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items__product", "payment_attempts"), pk=pk, user=request.user)
    return render(request, "orders/detail.html", {"order": order})


@login_required
def order_cancel(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status != Order.Status.CREATED:
        messages.error(request, "Покупатель может отменить только неоплаченный заказ.")
    else:
        try:
            cancel_order(order, request.user)
            messages.success(request, "Заказ отменён, товары возвращены на склад.")
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
    return redirect("orders:detail", pk=pk)
