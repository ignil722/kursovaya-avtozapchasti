from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from orders.models import Order

from .forms import ProductQuestionForm, ProductReviewForm
from .models import Category, Manufacturer, Product, ProductQuestion, ProductReview, Wishlist


def product_list(request):
    products = Product.objects.filter(is_active=True, category__is_active=True, manufacturer__is_active=True).select_related("category", "manufacturer")
    products = products.annotate(
        sold_count=Coalesce(
            Sum("order_items__quantity", filter=Q(order_items__order__status__in=(Order.Status.PAID, Order.Status.DELIVERED))),
            0,
        )
    )
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    manufacturer = request.GET.get("manufacturer", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "popular")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query) | Q(manufacturer__name__icontains=query))
    if category:
        products = products.filter(category__slug=category)
    if manufacturer:
        products = products.filter(manufacturer_id=manufacturer)
    try:
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
    except (TypeError, ValueError, ValidationError):
        messages.warning(request, "Проверьте диапазон цены.")
    ordering = {"popular": ("-sold_count", "name"), "price_asc": ("price", "name"), "price_desc": ("-price", "name"), "newest": ("-created_at",)}
    products = products.order_by(*ordering.get(sort, ordering["popular"]))
    page = Paginator(products, 8).get_page(request.GET.get("page"))
    favorites = set()
    if request.user.is_authenticated:
        favorites = set(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))
    return render(
        request,
        "catalog/product_list.html",
        {
            "page_obj": page,
            "categories": Category.objects.filter(is_active=True),
            "manufacturers": Manufacturer.objects.filter(is_active=True),
            "favorites": favorites,
            "filters": request.GET,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "manufacturer"), slug=slug, is_active=True)
    is_favorite = request.user.is_authenticated and Wishlist.objects.filter(user=request.user, product=product).exists()
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk).select_related("manufacturer")[:4]
    reviews = product.reviews.filter(is_published=True).select_related("user", "replied_by")
    questions = product.questions.filter(is_published=True).select_related("user", "answered_by")
    review_form = ProductReviewForm()
    if request.user.is_authenticated and not request.user.is_store_admin:
        existing_review = ProductReview.objects.filter(product=product, user=request.user).first()
        if existing_review:
            review_form = ProductReviewForm(instance=existing_review)
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "is_favorite": is_favorite,
            "related": related,
            "reviews": reviews,
            "questions": questions,
            "review_form": review_form,
            "question_form": ProductQuestionForm(),
        },
    )


@login_required
def wishlist(request):
    if request.user.is_store_admin:
        return redirect("staff:product_list")
    items = Wishlist.objects.filter(user=request.user).select_related("product__category", "product__manufacturer")
    return render(request, "catalog/wishlist.html", {"items": items})


@login_required
def toggle_wishlist(request, product_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.user.is_store_admin:
        messages.info(request, "Избранное доступно покупателям. Используйте управление каталогом.")
        return redirect("staff:product_list")
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, "Товар удалён из избранного.")
    else:
        messages.success(request, "Товар добавлен в избранное.")
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect(product.get_absolute_url())


@login_required
def submit_review(request, slug):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.user.is_store_admin:
        messages.info(request, "Администратор отвечает на отзывы из панели управления.")
        return redirect(f"{product.get_absolute_url()}#reviews")
    review = ProductReview.objects.filter(product=product, user=request.user).first()
    form = ProductReviewForm(request.POST, instance=review)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.is_published = True
        review.save()
        messages.success(request, "Ваш отзыв сохранён.")
    else:
        messages.error(request, "Проверьте оценку и текст отзыва.")
    return redirect(f"{product.get_absolute_url()}#reviews")


@login_required
def submit_question(request, slug):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.user.is_store_admin:
        messages.info(request, "Администратор отвечает на вопросы из панели управления.")
        return redirect(f"{product.get_absolute_url()}#questions")
    form = ProductQuestionForm(request.POST)
    if form.is_valid():
        question = form.save(commit=False)
        question.product = product
        question.user = request.user
        question.save()
        messages.success(request, "Вопрос отправлен магазину.")
    else:
        messages.error(request, "Введите текст вопроса.")
    return redirect(f"{product.get_absolute_url()}#questions")
