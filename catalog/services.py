from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Product, StockMovement


@transaction.atomic
def adjust_stock(product, delta, user=None, note=""):
    product = Product.objects.select_for_update().get(pk=product.pk)
    new_stock = product.stock + delta
    if new_stock < 0:
        raise ValidationError("Остаток не может быть отрицательным.")
    Product.objects.filter(pk=product.pk).update(stock=F("stock") + delta)
    StockMovement.objects.create(
        product=product,
        delta=delta,
        reason=StockMovement.Reason.ADJUSTMENT,
        created_by=user,
        note=note,
    )
    product.refresh_from_db(fields=("stock",))
    return product
