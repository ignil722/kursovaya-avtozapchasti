from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


def send_order_confirmation(order_id):
    order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    lines = [f"Здравствуйте, {order.user.first_name or order.user.username}!", "", f"Заказ {order.number} оформлен."]
    for item in order.items.all():
        lines.append(f"- {item.product_name}: {item.quantity} шт. x {item.unit_price} руб.")
    lines.extend(("", f"Итого: {order.total} руб.", f"Адрес: {order.delivery_address}", "Перейдите в личный кабинет для тестовой оплаты."))
    send_mail(
        subject=f"AutoParts Hub — заказ {order.number}",
        message="\n".join(lines),
        from_email=None,
        recipient_list=[order.user.email],
        fail_silently=True,
    )


@receiver(post_save, sender=Order)
def order_created_email(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: send_order_confirmation(instance.pk))
