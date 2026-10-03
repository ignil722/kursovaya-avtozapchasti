from django.urls import path

from . import views


app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("product/<str:slug>/", views.product_detail, name="detail"),
    path("product/<str:slug>/review/", views.submit_review, name="submit_review"),
    path("product/<str:slug>/question/", views.submit_question, name="submit_question"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/<int:product_id>/toggle/", views.toggle_wishlist, name="toggle_wishlist"),
]
