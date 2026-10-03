from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import User


class StyledFormMixin:
    def apply_styles(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css


class RegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(label="Электронная почта", required=True)
    first_name = forms.CharField(label="Имя", max_length=150, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
        labels = {"username": "Логин"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "pattern": r"[\w.@+-]+"})
        self.fields["email"].widget.attrs["autocomplete"] = "email"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.BUYER
        if commit:
            user.save()
        return user


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class AdminProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("avatar", "username", "first_name", "last_name", "email")
        labels = {"username": "Логин", "first_name": "Имя", "last_name": "Фамилия"}
        widgets = {"avatar": forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["username"].help_text = "Используется для входа в панель управления."
        self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Эта почта уже используется другим пользователем.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and getattr(avatar, "size", 0) > 3 * 1024 * 1024:
            raise forms.ValidationError("Размер фотографии не должен превышать 3 МБ.")
        return avatar


class AdminPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
