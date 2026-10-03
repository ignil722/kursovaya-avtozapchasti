from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from catalog.models import Product


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart", verbose_name="покупатель")
    updated_at = models.DateTimeField("обновлена", auto_now=True)

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.select_related("product")), Decimal("0.00"))

    @property
    def item_count(self):
        return sum(self.items.values_list("quantity", flat=True))

    def __str__(self):
        return f"Корзина {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="корзина")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items", verbose_name="товар")
    quantity = models.PositiveIntegerField("количество", default=1, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "позиция корзины"
        verbose_name_plural = "позиции корзины"
        constraints = [
            models.UniqueConstraint(fields=("cart", "product"), name="unique_cart_product"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="cart_quantity_positive"),
        ]

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product} × {self.quantity}"


class Order(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        PAID = "paid", "Оплачен"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders", verbose_name="покупатель")
    status = models.CharField("статус", max_length=16, choices=Status.choices, default=Status.CREATED, db_index=True)
    delivery_address = models.CharField("адрес доставки", max_length=300)
    total = models.DecimalField("сумма", max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField("создан", auto_now_add=True, db_index=True)
    paid_at = models.DateTimeField("оплачен", null=True, blank=True, db_index=True)
    delivered_at = models.DateTimeField("доставлен", null=True, blank=True)
    cancelled_at = models.DateTimeField("отменён", null=True, blank=True)
    restocked_at = models.DateTimeField("возвращён на склад", null=True, blank=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ("-created_at",)
        constraints = [models.CheckConstraint(condition=Q(total__gte=0), name="order_total_non_negative")]

    @property
    def number(self):
        return f"AP-{self.pk:06d}" if self.pk else "AP-NEW"

    def __str__(self):
        return f"{self.number} — {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="заказ")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items", verbose_name="товар")
    product_name = models.CharField("название", max_length=220)
    sku = models.CharField("артикул", max_length=64)
    unit_price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField("количество", validators=[MinValueValidator(1)])
    subtotal = models.DecimalField("сумма", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name="order_item_quantity_positive")]

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class PaymentAttempt(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Успешно"
        FAILED = "failed", "Отклонено"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_attempts", verbose_name="заказ")
    status = models.CharField("результат", max_length=12, choices=Status.choices)
    card_last4 = models.CharField("последние 4 цифры", max_length=4)
    failure_reason = models.CharField("причина отказа", max_length=255, blank=True)
    created_at = models.DateTimeField("дата", auto_now_add=True)

    class Meta:
        verbose_name = "попытка оплаты"
        verbose_name_plural = "попытки оплаты"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order.number}: {self.get_status_display()}"
