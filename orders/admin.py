from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem, PaymentAttempt


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "sku", "unit_price", "quantity", "subtotal")


class PaymentAttemptInline(admin.TabularInline):
    model = PaymentAttempt
    extra = 0
    can_delete = False
    readonly_fields = ("status", "card_last4", "failure_reason", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email", "delivery_address")
    readonly_fields = ("user", "status", "total", "delivery_address", "created_at", "paid_at", "delivered_at", "cancelled_at", "restocked_at")
    inlines = (OrderItemInline, PaymentAttemptInline)


admin.site.register(Cart)
admin.site.register(CartItem)
