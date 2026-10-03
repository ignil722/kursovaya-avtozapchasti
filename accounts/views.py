from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render

from .decorators import staff_required
from .forms import AdminPasswordChangeForm, AdminProfileForm, RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:list")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Аккаунт создан. Теперь войдите в систему.")
        return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


@staff_required
def admin_profile(request):
    profile_form = AdminProfileForm(instance=request.user)
    password_form = AdminPasswordChangeForm(request.user)
    if request.method == "POST" and "save_profile" in request.POST:
        profile_form = AdminProfileForm(request.POST, request.FILES, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Профиль администратора обновлён.")
            return redirect("accounts:admin_profile")
    elif request.method == "POST" and "change_password" in request.POST:
        password_form = AdminPasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль изменён. Вы остались в системе.")
            return redirect("accounts:admin_profile")
    return render(request, "accounts/admin_profile.html", {"profile_form": profile_form, "password_form": password_form})
