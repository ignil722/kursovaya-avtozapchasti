from datetime import timedelta

from django import forms
from django.utils import timezone


class ReportFilterForm(forms.Form):
    date_from = forms.DateField(label="Начало периода", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    date_to = forms.DateField(label="Конец периода", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    stock_date = forms.DateField(label="Остатки на дату", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))

    def __init__(self, *args, **kwargs):
        if not args and "data" not in kwargs:
            today = timezone.localdate()
            kwargs["initial"] = {"date_from": today - timedelta(days=29), "date_to": today, "stock_date": today}
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("date_from") and cleaned.get("date_to") and cleaned["date_from"] > cleaned["date_to"]:
            self.add_error("date_to", "Конец периода не может быть раньше начала.")
        return cleaned
