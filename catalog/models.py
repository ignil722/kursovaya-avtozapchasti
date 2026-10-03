from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify


def unique_slug(instance, value):
    base = slugify(value, allow_unicode=True) or "item"
    slug = base
    index = 2
    queryset = instance.__class__.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=slug).exists():
        slug = f"{base}-{index}"
        index += 1
    return slug


class Category(models.Model):
    name = models.CharField("название", max_length=120, unique=True)
    slug = models.SlugField("URL", max_length=140, unique=True, allow_unicode=True, blank=True)
    description = models.TextField("описание", blank=True)
    is_active = models.BooleanField("активна", default=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField("название", max_length=120, unique=True)
    country = models.CharField("страна", max_length=120)
    is_active = models.BooleanField("активен", default=True)

    class Meta:
        verbose_name = "производитель"
        verbose_name_plural = "производители"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=220)
    slug = models.SlugField("URL", max_length=240, unique=True, allow_unicode=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name="категория")
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name="products", verbose_name="производитель")
    sku = models.CharField("артикул", max_length=64, unique=True)
    price = models.DecimalField("цена", max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    stock = models.PositiveIntegerField("остаток", default=0)
    description = models.TextField("описание")
    image = models.ImageField("фотография", upload_to="products/%Y/%m/", blank=True)
    rating = models.DecimalField("рейтинг", max_digits=2, decimal_places=1, default=Decimal("4.8"), validators=[MinValueValidator(0), MaxValueValidator(5)])
    is_active = models.BooleanField("активен", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ("name",)
        constraints = [
            models.CheckConstraint(condition=Q(price__gt=0), name="product_price_positive"),
            models.CheckConstraint(condition=Q(stock__gte=0), name="product_stock_non_negative"),
        ]

    def save(self, *args, **kwargs):
        adding = self._state.adding
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)
        if adding and self.stock:
            StockMovement.objects.create(product=self, delta=self.stock, reason=StockMovement.Reason.INITIAL, note="Начальный остаток")

    def get_absolute_url(self):
        return reverse("catalog:detail", kwargs={"slug": self.slug})

    @property
    def category_code(self):
        mapping = {"Тормоза": "BRK", "Фильтры": "FIL", "Зажигание": "IGN", "Подвеска": "SUS", "Электрика": "ELC", "Масла и жидкости": "FLD"}
        return mapping.get(self.category.name, "PRT")

    def __str__(self):
        return f"{self.name} ({self.sku})"


class StockMovement(models.Model):
    class Reason(models.TextChoices):
        INITIAL = "initial", "Начальный остаток"
        ADJUSTMENT = "adjustment", "Корректировка"
        ORDER = "order", "Резерв по заказу"
        CANCELLATION = "cancellation", "Возврат при отмене"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_movements", verbose_name="товар")
    delta = models.IntegerField("изменение")
    reason = models.CharField("причина", max_length=20, choices=Reason.choices)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements", verbose_name="заказ")
    note = models.CharField("примечание", max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements", verbose_name="сотрудник")
    created_at = models.DateTimeField("дата", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "движение по складу"
        verbose_name_plural = "движения по складу"
        ordering = ("-created_at", "-pk")
        constraints = [models.CheckConstraint(condition=~Q(delta=0), name="stock_movement_delta_not_zero")]

    def __str__(self):
        sign = "+" if self.delta > 0 else ""
        return f"{self.product.sku}: {sign}{self.delta}"


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items", verbose_name="покупатель")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by", verbose_name="товар")
    created_at = models.DateTimeField("добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "избранный товар"
        verbose_name_plural = "избранное"
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("user", "product"), name="unique_wishlist_product")]

    def __str__(self):
        return f"{self.user}: {self.product}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="товар")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_reviews", verbose_name="покупатель")
    rating = models.PositiveSmallIntegerField("оценка", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("отзыв", max_length=2000)
    admin_reply = models.TextField("ответ магазина", max_length=2000, blank=True)
    replied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="review_replies", verbose_name="ответил")
    replied_at = models.DateTimeField("дата ответа", null=True, blank=True)
    is_published = models.BooleanField("опубликован", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    class Meta:
        verbose_name = "отзыв о товаре"
        verbose_name_plural = "отзывы о товарах"
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("product", "user"), name="unique_product_review_per_user")]

    @property
    def is_answered(self):
        return bool(self.admin_reply)

    def __str__(self):
        return f"{self.product.name}: {self.user} — {self.rating}/5"


class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="questions", verbose_name="товар")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_questions", verbose_name="покупатель")
    text = models.TextField("вопрос", max_length=2000)
    answer = models.TextField("ответ магазина", max_length=2000, blank=True)
    answered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="question_answers", verbose_name="ответил")
    answered_at = models.DateTimeField("дата ответа", null=True, blank=True)
    is_published = models.BooleanField("опубликован", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "вопрос о товаре"
        verbose_name_plural = "вопросы о товарах"
        ordering = ("-created_at",)

    @property
    def is_answered(self):
        return bool(self.answer)

    def __str__(self):
        return f"{self.product.name}: {self.user}"
