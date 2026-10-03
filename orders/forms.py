import re
from datetime import date

from django import forms


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        label="Адрес доставки",
        min_length=5,
        max_length=300,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "required": True, "placeholder": "Город, улица, дом, квартира"}),
    )


class PaymentForm(forms.Form):
    cardholder = forms.CharField(label="Имя на карте", max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "cc-name"}))
    card_number = forms.CharField(label="Номер тестовой карты", max_length=19, widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "autocomplete": "cc-number", "pattern": r"[0-9 ]{16,19}", "placeholder": "4242 4242 4242 4242"}))
    expiry = forms.CharField(label="Срок", max_length=5, widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "pattern": r"(0[1-9]|1[0-2])/[0-9]{2}", "placeholder": "12/30"}))
    cvv = forms.CharField(label="CVV", max_length=3, widget=forms.PasswordInput(attrs={"class": "form-control", "inputmode": "numeric", "pattern": r"[0-9]{3}", "autocomplete": "cc-csc"}))

    def clean_card_number(self):
        number = re.sub(r"\s+", "", self.cleaned_data["card_number"])
        if not number.isdigit() or len(number) != 16 or not self._luhn(number):
            raise forms.ValidationError("Введите корректный 16-значный номер карты.")
        if number not in {"4242424242424242", "4000000000000002"}:
            raise forms.ValidationError("Используйте одну из тестовых карт, указанных на странице.")
        return number

    def clean_expiry(self):
        value = self.cleaned_data["expiry"]
        match = re.fullmatch(r"(0[1-9]|1[0-2])/(\d{2})", value)
        if not match:
            raise forms.ValidationError("Формат срока: ММ/ГГ.")
        month, year = int(match.group(1)), 2000 + int(match.group(2))
        today = date.today()
        if (year, month) < (today.year, today.month):
            raise forms.ValidationError("Срок действия карты истёк.")
        return value

    def clean_cvv(self):
        value = self.cleaned_data["cvv"]
        if not value.isdigit() or len(value) != 3:
            raise forms.ValidationError("CVV должен содержать 3 цифры.")
        return value

    @staticmethod
    def _luhn(number):
        digits = [int(char) for char in number]
        checksum = 0
        parity = len(digits) % 2
        for index, digit in enumerate(digits):
            if index % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(label="Новый статус", choices=(), widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        transitions = {
            "created": (("paid", "Оплачен"), ("cancelled", "Отменён")),
            "paid": (("delivered", "Доставлен"), ("cancelled", "Отменён")),
        }
        self.fields["status"].choices = transitions.get(order.status if order else "", ())
