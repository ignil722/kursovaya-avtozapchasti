from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import staff_required

from .forms import CategoryForm, FeedbackReplyForm, ManufacturerForm, ProductForm, StockAdjustmentForm
from .models import Category, Manufacturer, Product, ProductQuestion, ProductReview, StockMovement
from .services import adjust_stock


@staff_required
def category_list(request):
    return render(request, "staff/entity_list.html", {"objects": Category.objects.all(), "entity": "category", "title": "Категории"})


@staff_required
def category_form(request, pk=None):
    instance = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категория сохранена.")
        return redirect("staff:category_list")
    return render(request, "staff/entity_form.html", {"form": form, "title": "Категория", "cancel_url": "staff:category_list"})


@staff_required
def category_delete(request, pk):
    return _delete_entity(request, get_object_or_404(Category, pk=pk), "staff:category_list", "категорию")


@staff_required
def manufacturer_list(request):
    return render(request, "staff/entity_list.html", {"objects": Manufacturer.objects.all(), "entity": "manufacturer", "title": "Производители"})


@staff_required
def manufacturer_form(request, pk=None):
    instance = get_object_or_404(Manufacturer, pk=pk) if pk else None
    form = ManufacturerForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Производитель сохранён.")
        return redirect("staff:manufacturer_list")
    return render(request, "staff/entity_form.html", {"form": form, "title": "Производитель", "cancel_url": "staff:manufacturer_list"})


@staff_required
def manufacturer_delete(request, pk):
    return _delete_entity(request, get_object_or_404(Manufacturer, pk=pk), "staff:manufacturer_list", "производителя")


@staff_required
def product_list(request):
    products = Product.objects.select_related("category", "manufacturer")
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query) | Q(manufacturer__name__icontains=query))
    return render(request, "staff/product_list.html", {"objects": products, "query": query})


@staff_required
def product_form(request, pk=None):
    instance = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        if not instance:
            product.stock = 0
        product.save()
        messages.success(request, "Товар сохранён. Остаток изменяется отдельной операцией.")
        return redirect("staff:product_list")
    return render(request, "staff/entity_form.html", {"form": form, "title": "Товар", "cancel_url": "staff:product_list"})


@staff_required
def product_delete(request, pk):
    return _delete_entity(request, get_object_or_404(Product, pk=pk), "staff:product_list", "товар")


@staff_required
def stock_adjustment(request):
    form = StockAdjustmentForm(request.POST or None, initial={"product": request.GET.get("product")})
    if request.method == "POST" and form.is_valid():
        adjust_stock(form.cleaned_data["product"], form.cleaned_data["delta"], request.user, form.cleaned_data["note"])
        messages.success(request, "Остаток обновлён и записан в журнал.")
        return redirect("staff:stock_adjustment")
    movements = StockMovement.objects.select_related("product", "created_by")[:30]
    return render(request, "staff/stock_adjustment.html", {"form": form, "movements": movements})


@staff_required
def feedback_list(request):
    status = request.GET.get("status", "unanswered")
    kind = request.GET.get("kind", "all")
    query = request.GET.get("q", "").strip()
    reviews = ProductReview.objects.select_related("product", "user", "replied_by")
    questions = ProductQuestion.objects.select_related("product", "user", "answered_by")
    if status == "unanswered":
        reviews = reviews.filter(admin_reply="")
        questions = questions.filter(answer="")
    elif status == "answered":
        reviews = reviews.exclude(admin_reply="")
        questions = questions.exclude(answer="")
    if query:
        review_filter = Q(product__name__icontains=query) | Q(user__username__icontains=query) | Q(text__icontains=query)
        question_filter = Q(product__name__icontains=query) | Q(user__username__icontains=query) | Q(text__icontains=query)
        reviews = reviews.filter(review_filter)
        questions = questions.filter(question_filter)
    if kind == "reviews":
        questions = questions.none()
    elif kind == "questions":
        reviews = reviews.none()
    return render(
        request,
        "staff/feedback_list.html",
        {
            "reviews": reviews,
            "questions": questions,
            "selected_status": status,
            "selected_kind": kind,
            "query": query,
            "unanswered_reviews": ProductReview.objects.filter(admin_reply="").count(),
            "unanswered_questions": ProductQuestion.objects.filter(answer="").count(),
        },
    )


@staff_required
def reply_review(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    review = get_object_or_404(ProductReview, pk=pk)
    form = FeedbackReplyForm(request.POST)
    if form.is_valid():
        review.admin_reply = form.cleaned_data["reply"]
        review.is_published = form.cleaned_data["is_published"]
        review.replied_by = request.user
        review.replied_at = timezone.now()
        review.save(update_fields=("admin_reply", "is_published", "replied_by", "replied_at", "updated_at"))
        messages.success(request, "Ответ на отзыв опубликован.")
    else:
        messages.error(request, "Введите ответ длиной до 2000 символов.")
    return redirect(f"{reverse('staff:feedback')}?status=all#review-{review.pk}")


@staff_required
def reply_question(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    question = get_object_or_404(ProductQuestion, pk=pk)
    form = FeedbackReplyForm(request.POST)
    if form.is_valid():
        question.answer = form.cleaned_data["reply"]
        question.is_published = form.cleaned_data["is_published"]
        question.answered_by = request.user
        question.answered_at = timezone.now()
        question.save(update_fields=("answer", "is_published", "answered_by", "answered_at"))
        messages.success(request, "Ответ на вопрос опубликован.")
    else:
        messages.error(request, "Введите ответ длиной до 2000 символов.")
    return redirect(f"{reverse('staff:feedback')}?status=all#question-{question.pk}")


def _delete_entity(request, obj, redirect_name, label):
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, f"Удалено: {obj}.")
        except ProtectedError:
            messages.error(request, f"Нельзя удалить {label}: объект используется в каталоге или заказах.")
        return redirect(redirect_name)
    return render(request, "staff/confirm_delete.html", {"object": obj, "cancel_url": redirect_name})
