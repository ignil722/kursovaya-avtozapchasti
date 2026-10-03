from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Администратор"
        BUYER = "buyer", "Покупатель"

    email = models.EmailField("электронная почта", unique=True)
    role = models.CharField("роль", max_length=10, choices=Role.choices, default=Role.BUYER)
    avatar = models.ImageField("фотография профиля", upload_to="avatars/%Y/%m/", blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser or self.is_staff:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_store_admin(self):
        return self.is_authenticated and (self.is_staff or self.role == self.Role.ADMIN)

    def __str__(self):
        return self.get_full_name() or self.username
