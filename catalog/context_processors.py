def store_context(request):
    cart_count = 0
    if request.user.is_authenticated:
        from orders.models import CartItem

        cart_count = sum(CartItem.objects.filter(cart__user=request.user).values_list("quantity", flat=True))
    return {"cart_count": cart_count}
