from django.urls import path

from catalog import staff_views as catalog_views
from orders import staff_views as order_views
from reports import views as report_views


app_name = "staff"

urlpatterns = [
    path("", report_views.dashboard, name="dashboard"),
    path("categories/", catalog_views.category_list, name="category_list"),
    path("categories/add/", catalog_views.category_form, name="category_add"),
    path("categories/<int:pk>/edit/", catalog_views.category_form, name="category_edit"),
    path("categories/<int:pk>/delete/", catalog_views.category_delete, name="category_delete"),
    path("manufacturers/", catalog_views.manufacturer_list, name="manufacturer_list"),
    path("manufacturers/add/", catalog_views.manufacturer_form, name="manufacturer_add"),
    path("manufacturers/<int:pk>/edit/", catalog_views.manufacturer_form, name="manufacturer_edit"),
    path("manufacturers/<int:pk>/delete/", catalog_views.manufacturer_delete, name="manufacturer_delete"),
    path("products/", catalog_views.product_list, name="product_list"),
    path("products/add/", catalog_views.product_form, name="product_add"),
    path("products/<int:pk>/edit/", catalog_views.product_form, name="product_edit"),
    path("products/<int:pk>/delete/", catalog_views.product_delete, name="product_delete"),
    path("stock/adjust/", catalog_views.stock_adjustment, name="stock_adjustment"),
    path("feedback/", catalog_views.feedback_list, name="feedback"),
    path("feedback/reviews/<int:pk>/reply/", catalog_views.reply_review, name="reply_review"),
    path("feedback/questions/<int:pk>/reply/", catalog_views.reply_question, name="reply_question"),
    path("orders/", order_views.order_list, name="order_list"),
    path("orders/<int:pk>/", order_views.order_detail, name="order_detail"),
    path("reports/", report_views.reports_view, name="reports"),
]
