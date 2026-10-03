from django.contrib import admin

from .models import Category, Manufacturer, Product, ProductQuestion, ProductReview, StockMovement, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active")
    list_filter = ("country", "is_active")
    search_fields = ("name", "country")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "manufacturer", "price", "stock", "is_active")
    list_filter = ("category", "manufacturer", "is_active")
    search_fields = ("name", "sku", "manufacturer__name")
    readonly_fields = ("stock", "created_at", "updated_at")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "delta", "reason", "order", "created_by", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("product__name", "product__sku", "note")
    readonly_fields = ("product", "delta", "reason", "order", "created_by", "note", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Wishlist)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_published", "replied_by", "created_at")
    list_filter = ("rating", "is_published", "created_at")
    search_fields = ("product__name", "user__username", "text", "admin_reply")


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "is_published", "answered_by", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("product__name", "user__username", "text", "answer")
