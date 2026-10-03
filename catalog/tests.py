from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Category, Manufacturer, Product, ProductQuestion, ProductReview, StockMovement, Wishlist
from .services import adjust_stock


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Тормоза", description="Тормозная система")
        cls.other_category = Category.objects.create(name="Фильтры")
        cls.manufacturer = Manufacturer.objects.create(name="Brembo", country="Италия")
        cls.other_manufacturer = Manufacturer.objects.create(name="Bosch", country="Германия")
        cls.product = Product.objects.create(name="Колодки Brembo", category=cls.category, manufacturer=cls.manufacturer, sku="BR-1", price=Decimal("1000.00"), stock=5, description="Керамические колодки")
        cls.other_product = Product.objects.create(name="Фильтр Bosch", category=cls.other_category, manufacturer=cls.other_manufacturer, sku="BO-2", price=Decimal("500.00"), stock=12, description="Масляный фильтр")
        cls.buyer = User.objects.create_user(username="buyer", email="buyer@example.com", password="pass12345")
        cls.admin = User.objects.create_user(username="admin", email="admin@example.com", password="pass12345", is_staff=True)

    def test_initial_stock_creates_ledger_entry(self):
        movement = StockMovement.objects.get(product=self.product, reason=StockMovement.Reason.INITIAL)
        self.assertEqual(movement.delta, 5)

    def test_product_rejects_non_positive_price(self):
        self.product.price = Decimal("0")
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_stock_adjustment_updates_stock_and_ledger(self):
        adjust_stock(self.product, -2, self.admin, "Инвентаризация")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertTrue(StockMovement.objects.filter(product=self.product, delta=-2, note="Инвентаризация").exists())

    def test_stock_adjustment_never_makes_negative_stock(self):
        with self.assertRaises(ValidationError):
            adjust_stock(self.product, -6, self.admin)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_catalog_search_filter_and_sort(self):
        response = self.client.get(reverse("catalog:list"), {"q": "BR-1", "category": self.category.slug, "manufacturer": self.manufacturer.pk, "min_price": "900", "max_price": "1100", "sort": "price_desc"})
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, self.other_product.name)

    def test_invalid_price_filter_does_not_break_catalog(self):
        response = self.client.get(reverse("catalog:list"), {"min_price": "not-a-price"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Проверьте диапазон цены.")

    def test_catalog_navigation_keeps_catalog_anchor(self):
        response = self.client.get(reverse("catalog:list"))
        self.assertContains(response, 'id="catalog"')
        self.assertContains(response, "#catalog", count=None)
        self.assertContains(response, "data-catalog-navigation", count=None)

    def test_wishlist_is_isolated_by_user(self):
        Wishlist.objects.create(user=self.buyer, product=self.product)
        other = User.objects.create_user(username="other", email="other@example.com", password="pass12345")
        self.client.force_login(other)
        response = self.client.get(reverse("catalog:wishlist"))
        self.assertNotContains(response, self.product.name)

    def test_buyer_cannot_open_staff_pages(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("staff:product_list")).status_code, 403)

    def test_admin_can_open_staff_crud(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("staff:product_list")).status_code, 200)

    def test_admin_wishlist_redirects_to_catalog_management(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse("catalog:wishlist")), reverse("staff:product_list"))

    def test_buyer_can_leave_and_update_single_review(self):
        self.client.force_login(self.buyer)
        url = reverse("catalog:submit_review", args=(self.product.slug,))
        self.client.post(url, {"rating": 5, "text": "Отличные колодки, всё подошло."})
        self.client.post(url, {"rating": 4, "text": "Дополняю отзыв после недели эксплуатации."})
        self.assertEqual(ProductReview.objects.filter(product=self.product, user=self.buyer).count(), 1)
        self.assertEqual(ProductReview.objects.get(product=self.product, user=self.buyer).rating, 4)

    def test_buyer_can_ask_question_and_admin_can_answer(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("catalog:submit_question", args=(self.product.slug,)), {"text": "Подойдёт ли к моей машине?"})
        question = ProductQuestion.objects.get(product=self.product, user=self.buyer)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("staff:reply_question", args=(question.pk,)), {"reply": "Да, проверьте артикул по VIN.", "is_published": "on"})
        self.assertEqual(response.status_code, 302)
        question.refresh_from_db()
        self.assertEqual(question.answer, "Да, проверьте артикул по VIN.")
        self.assertEqual(question.answered_by, self.admin)
        self.assertIsNotNone(question.answered_at)

    def test_admin_can_answer_review_from_feedback_panel(self):
        review = ProductReview.objects.create(product=self.product, user=self.buyer, rating=5, text="Хороший товар")
        self.client.force_login(self.admin)
        self.client.post(reverse("staff:reply_review", args=(review.pk,)), {"reply": "Спасибо за ваш отзыв!", "is_published": "on"})
        review.refresh_from_db()
        self.assertEqual(review.admin_reply, "Спасибо за ваш отзыв!")
        self.assertEqual(review.replied_by, self.admin)
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "Спасибо за ваш отзыв!")

    def test_buyer_cannot_open_feedback_panel(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("staff:feedback")).status_code, 403)
