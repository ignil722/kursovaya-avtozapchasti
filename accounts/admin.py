from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class StoreUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Магазин", {"fields": ("role", "avatar")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Магазин", {"fields": ("email", "role", "avatar")}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = UserAdmin.list_filter + ("role",)
    search_fields = ("username", "first_name", "last_name", "email")
