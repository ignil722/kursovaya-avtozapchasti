from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Product, StockMovement

from .models import Cart, CartItem, Order, OrderItem, PaymentAttempt


class StockError(ValidationError):
    pass


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@transaction.atomic
def add_to_cart(user, product, quantity=1):
    if quantity < 1:
        raise ValidationError("Количество должно быть положительным.")
    product = Product.objects.get(pk=product.pk, is_active=True)
    cart = get_cart(user)
    item, created = CartItem.objects.select_for_update().get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    desired = quantity if created else item.quantity + quantity
    if desired > product.stock:
        raise StockError(f"Доступно только {product.stock} шт.")
    if not created:
        item.quantity = desired
        item.full_clean()
        item.save(update_fields=("quantity",))
    return item


@transaction.atomic
def create_order(user, delivery_address):
    cart = Cart.objects.select_for_update().filter(user=user).first()
    if not cart:
        raise ValidationError("Корзина пуста.")
    cart_items = list(CartItem.objects.select_for_update().filter(cart=cart).select_related("product").order_by("product_id"))
    if not cart_items:
        raise ValidationError("Корзина пуста.")
    products = {product.pk: product for product in Product.objects.select_for_update().filter(pk__in=[item.product_id for item in cart_items]).order_by("pk")}
    order = Order.objects.create(user=user, delivery_address=delivery_address, total=0)
    total = Decimal("0.00")
    order_items = []
    movements = []
    for cart_item in cart_items:
        product = products[cart_item.product_id]
        if not product.is_active or product.stock < cart_item.quantity:
            raise StockError(f"Для «{product.name}» доступно только {product.stock} шт.")
        updated = Product.objects.filter(pk=product.pk, stock__gte=cart_item.quantity).update(stock=F("stock") - cart_item.quantity)
        if updated != 1:
            raise StockError(f"Остаток «{product.name}» изменился. Обновите корзину.")
        subtotal = product.price * cart_item.quantity
        total += subtotal
        order_items.append(OrderItem(order=order, product=product, product_name=product.name, sku=product.sku, unit_price=product.price, quantity=cart_item.quantity, subtotal=subtotal))
        movements.append(StockMovement(product=product, delta=-cart_item.quantity, reason=StockMovement.Reason.ORDER, order=order, note=f"Резерв по заказу {order.number}"))
    OrderItem.objects.bulk_create(order_items)
    StockMovement.objects.bulk_create(movements)
    order.total = total
    order.save(update_fields=("total",))
    CartItem.objects.filter(cart=cart).delete()
    return order


@transaction.atomic
def process_payment(order, card_number):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.CREATED:
        raise ValidationError("Этот заказ уже обработан.")
    success = card_number == "4242424242424242"
    attempt = PaymentAttempt.objects.create(
        order=order,
        status=PaymentAttempt.Status.SUCCESS if success else PaymentAttempt.Status.FAILED,
        card_last4=card_number[-4:],
        failure_reason="Тестовый отказ банка" if not success else "",
    )
    if success:
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=("status", "paid_at"))
    return attempt


@transaction.atomic
def cancel_order(order, actor=None):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status not in (Order.Status.CREATED, Order.Status.PAID):
        raise ValidationError("Заказ в этом статусе нельзя отменить.")
    if not order.restocked_at:
        for item in order.items.select_related("product").select_for_update():
            Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
            StockMovement.objects.create(product=item.product, delta=item.quantity, reason=StockMovement.Reason.CANCELLATION, order=order, created_by=actor, note=f"Возврат по отменённому заказу {order.number}")
        order.restocked_at = timezone.now()
    order.status = Order.Status.CANCELLED
    order.cancelled_at = timezone.now()
    order.save(update_fields=("status", "cancelled_at", "restocked_at"))
    return order


@transaction.atomic
def transition_order(order, new_status, actor=None):
    order = Order.objects.select_for_update().get(pk=order.pk)
    allowed = {Order.Status.CREATED: {Order.Status.PAID, Order.Status.CANCELLED}, Order.Status.PAID: {Order.Status.DELIVERED, Order.Status.CANCELLED}}
    if new_status not in allowed.get(order.status, set()):
        raise ValidationError("Недопустимый переход статуса.")
    if new_status == Order.Status.CANCELLED:
        return cancel_order(order, actor)
    now = timezone.now()
    order.status = new_status
    fields = ["status"]
    if new_status == Order.Status.PAID:
        order.paid_at = now
        fields.append("paid_at")
    elif new_status == Order.Status.DELIVERED:
        order.delivered_at = now
        fields.append("delivered_at")
    order.save(update_fields=fields)
    return order
