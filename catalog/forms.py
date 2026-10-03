from django import forms

from .models import Category, Manufacturer, Product, ProductQuestion, ProductReview


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"


class CategoryForm(BootstrapModelForm):
    class Meta:
        model = Category
        fields = ("name", "description", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class ManufacturerForm(BootstrapModelForm):
    class Meta:
        model = Manufacturer
        fields = ("name", "country", "is_active")


class ProductForm(BootstrapModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "manufacturer", "sku", "price", "description", "image", "rating", "is_active")
        widgets = {
            "price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "rating": forms.NumberInput(attrs={"min": "0", "max": "5", "step": "0.1"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(label="Товар", queryset=Product.objects.none())
    delta = forms.IntegerField(label="Изменение", help_text="Положительное число — приход, отрицательное — списание.")
    note = forms.CharField(label="Комментарий", max_length=255, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.select_related("manufacturer").order_by("name")
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"

    def clean_delta(self):
        delta = self.cleaned_data["delta"]
        if delta == 0:
            raise forms.ValidationError("Укажите ненулевое изменение.")
        return delta

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        delta = cleaned.get("delta")
        if product and delta is not None and product.stock + delta < 0:
            self.add_error("delta", f"На складе только {product.stock} шт.")
        return cleaned


class ProductReviewForm(BootstrapModelForm):
    class Meta:
        model = ProductReview
        fields = ("rating", "text")
        widgets = {
            "rating": forms.Select(choices=((5, "5 — Отлично"), (4, "4 — Хорошо"), (3, "3 — Нормально"), (2, "2 — Плохо"), (1, "1 — Очень плохо"))),
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Расскажите о качестве детали и опыте использования"}),
        }


class ProductQuestionForm(BootstrapModelForm):
    class Meta:
        model = ProductQuestion
        fields = ("text",)
        widgets = {"text": forms.Textarea(attrs={"rows": 3, "placeholder": "Например: подойдёт ли эта деталь к моему автомобилю?"})}


class FeedbackReplyForm(forms.Form):
    reply = forms.CharField(label="Ответ магазина", max_length=2000, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Введите официальный ответ магазина"}))
    is_published = forms.BooleanField(label="Показывать на странице товара", required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
