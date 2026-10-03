from datetime import date
from decimal import Decimal

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, Manufacturer, Product, StockMovement

from .forms import PaymentForm
from .models import CartItem, Order, PaymentAttempt
from .services import StockError, add_to_cart, cancel_order, create_order, get_cart, process_payment, transition_order


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", email="buyer@example.com", password="pass12345", first_name="Иван")
        self.other = User.objects.create_user(username="other", email="other@example.com", password="pass12345")
        self.admin = User.objects.create_user(username="admin", email="admin@example.com", password="pass12345", is_staff=True)
        category = Category.objects.create(name="Тормоза")
        manufacturer = Manufacturer.objects.create(name="Brembo", country="Италия")
        self.product = Product.objects.create(name="Колодки", category=category, manufacturer=manufacturer, sku="BR-1", price=Decimal("1000.00"), stock=5, description="Описание")
        self.second = Product.objects.create(name="Диск", category=category, manufacturer=manufacturer, sku="BR-2", price=Decimal("2000.00"), stock=1, description="Описание")

    def test_cart_rejects_more_than_stock(self):
        with self.assertRaises(StockError):
            add_to_cart(self.user, self.product, 6)

    def test_checkout_is_atomic_and_creates_snapshot_and_email(self):
        add_to_cart(self.user, self.product, 2)
        with self.captureOnCommitCallbacks(execute=True):
            order = create_order(self.user, "г. Муром, ул. Ленина, д. 1")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(order.total, Decimal("2000.00"))
        self.assertEqual(order.items.get().product_name, "Колодки")
        self.assertFalse(CartItem.objects.filter(cart__user=self.user).exists())
        self.assertTrue(StockMovement.objects.filter(order=order, delta=-2).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.number, mail.outbox[0].subject)

    def test_checkout_rolls_back_every_item_when_stock_is_missing(self):
        add_to_cart(self.user, self.product, 2)
        cart = get_cart(self.user)
        CartItem.objects.create(cart=cart, product=self.second, quantity=2)
        with self.assertRaises(StockError):
            create_order(self.user, "Адрес доставки")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(Order.objects.count(), 0)

    def test_successful_and_failed_payments(self):
        add_to_cart(self.user, self.product, 1)
        order = create_order(self.user, "Адрес доставки")
        failed = process_payment(order, "4000000000000002")
        order.refresh_from_db()
        self.assertEqual(failed.status, PaymentAttempt.Status.FAILED)
        self.assertEqual(order.status, Order.Status.CREATED)
        success = process_payment(order, "4242424242424242")
        order.refresh_from_db()
        self.assertEqual(success.status, PaymentAttempt.Status.SUCCESS)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNotNone(order.paid_at)

    def test_cancel_restock_is_applied_once(self):
        add_to_cart(self.user, self.product, 2)
        order = create_order(self.user, "Адрес доставки")
        cancel_order(order, self.user)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        with self.assertRaises(ValidationError):
            cancel_order(order, self.user)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(StockMovement.objects.filter(order=order, reason=StockMovement.Reason.CANCELLATION).count(), 1)

    def test_valid_status_transitions(self):
        add_to_cart(self.user, self.product, 1)
        order = create_order(self.user, "Адрес доставки")
        transition_order(order, Order.Status.PAID, self.admin)
        order.refresh_from_db()
        transition_order(order, Order.Status.DELIVERED, self.admin)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
        with self.assertRaises(ValidationError):
            transition_order(order, Order.Status.CANCELLED, self.admin)

    def test_another_user_cannot_view_order(self):
        add_to_cart(self.user, self.product, 1)
        order = create_order(self.user, "Адрес доставки")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("orders:detail", args=(order.pk,))).status_code, 404)

    def test_payment_form_validates_test_cards_and_expiry(self):
        future_year = (date.today().year + 2) % 100
        form = PaymentForm({"cardholder": "IVAN IVANOV", "card_number": "4242 4242 4242 4242", "expiry": f"12/{future_year:02d}", "cvv": "123"})
        self.assertTrue(form.is_valid(), form.errors)
        form = PaymentForm({"cardholder": "IVAN IVANOV", "card_number": "4111 1111 1111 1111", "expiry": f"12/{future_year:02d}", "cvv": "123"})
        self.assertFalse(form.is_valid())

    def test_admin_buyer_pages_redirect_to_order_management(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse("orders:history")), reverse("staff:order_list"))
        self.assertRedirects(self.client.get(reverse("orders:cart")), reverse("staff:order_list"))
