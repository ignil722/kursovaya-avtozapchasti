from django.urls import path

from . import views


app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/item/<int:item_id>/update/", views.cart_update, name="cart_update"),
    path("cart/item/<int:item_id>/remove/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("<int:pk>/payment/", views.payment, name="payment"),
    path("<int:pk>/cancel/", views.order_cancel, name="cancel"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("", views.order_history, name="history"),
]
