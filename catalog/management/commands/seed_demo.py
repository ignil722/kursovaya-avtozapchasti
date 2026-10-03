import os
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Manufacturer, Product, ProductQuestion, ProductReview, StockMovement
from orders.models import Order, PaymentAttempt
from orders.services import add_to_cart, cancel_order, create_order, process_payment, transition_order


class Command(BaseCommand):
    help = "Идемпотентно создаёт демонстрационный каталог, пользователей и заказы."

    def handle(self, *args, **options):
        admin_username = os.environ.get("DEMO_ADMIN_USERNAME", "admin")
        admin_email = os.environ.get("DEMO_ADMIN_EMAIL", "admin@autoparts.local")
        admin_password = os.environ.get("DEMO_ADMIN_PASSWORD", "Admin123!")
        admin = User.objects.filter(is_superuser=True).order_by("pk").first()
        admin_created = admin is None
        if admin is None:
            admin = User(username=admin_username, email=admin_email, first_name="Администратор", role=User.Role.ADMIN, is_staff=True, is_superuser=True)
            admin.set_password(admin_password)
            admin.save()
        else:
            changed_fields = []
            if not admin.is_staff or admin.role != User.Role.ADMIN:
                admin.is_staff = True
                admin.role = User.Role.ADMIN
                changed_fields.extend(("is_staff", "role"))
            if os.environ.get("DEMO_ADMIN_PASSWORD"):
                admin.set_password(admin_password)
                changed_fields.append("password")
            if changed_fields:
                admin.save(update_fields=changed_fields)
        buyer, created = User.objects.get_or_create(
            username="buyer",
            defaults={"email": "buyer@autoparts.local", "first_name": "Сергей", "last_name": "Терехов", "role": User.Role.BUYER},
        )
        if created:
            buyer.set_password("Buyer123!")
            buyer.save()

        category_names = {
            "brakes": ("Тормоза", "Колодки, диски и комплектующие тормозной системы"),
            "filters": ("Фильтры", "Воздушные, масляные и салонные фильтры"),
            "ignition": ("Зажигание", "Свечи, катушки и компоненты системы зажигания"),
            "suspension": ("Подвеска", "Амортизаторы, пружины и рычаги"),
            "electrical": ("Электрика", "Аккумуляторы, лампы и электрооборудование"),
            "fluids": ("Масла и жидкости", "Моторные масла и технические жидкости"),
        }
        categories = {}
        for key, (name, description) in category_names.items():
            categories[key], _ = Category.objects.get_or_create(name=name, defaults={"description": description})

        manufacturer_data = {"Brembo": "Италия", "Bosch": "Германия", "Denso": "Япония", "Bilstein": "Германия", "MANN-FILTER": "Германия", "Castrol": "Великобритания", "NGK": "Япония", "VARTA": "Германия"}
        manufacturers = {}
        for name, country in manufacturer_data.items():
            manufacturers[name], _ = Manufacturer.objects.get_or_create(name=name, defaults={"country": country})

        product_data = [
            ("Керамические тормозные колодки Brembo P 06 072", "BRM-P06072", "brakes", "Brembo", "6840.00", 18, "Малопыльный керамический состав для стабильного торможения и ежедневной эксплуатации.", "4.8"),
            ("Тормозной диск Bosch QuietCast", "BOS-BD1808", "brakes", "Bosch", "7280.00", 12, "Вентилируемый диск с антикоррозийным покрытием и точной заводской балансировкой.", "4.6"),
            ("Воздушный фильтр MANN-FILTER C 35 154", "MAN-C35154", "filters", "MANN-FILTER", "1850.00", 7, "Высокая степень фильтрации и надёжная защита двигателя от пыли.", "4.7"),
            ("Масляный фильтр Bosch P 3274", "BOS-P3274", "filters", "Bosch", "980.00", 46, "Синтетический фильтрующий материал для увеличенного интервала обслуживания.", "4.7"),
            ("Свечи зажигания Denso Iridium TT, 4 шт.", "DEN-4704", "ignition", "Denso", "3820.00", 31, "Иридиевые свечи с тонким электродом для уверенного запуска и чистого сгорания.", "4.9"),
            ("Свечи зажигания NGK Laser Platinum, 4 шт.", "NGK-3199", "ignition", "NGK", "4490.00", 16, "Платиновое покрытие и стабильная искра в широком диапазоне температур.", "4.8"),
            ("Амортизатор Bilstein B6", "BIL-24186742", "suspension", "Bilstein", "13900.00", 4, "Однотрубный газовый амортизатор для точного контроля кузова.", "4.6"),
            ("Комплект рычагов подвески Bosch", "BOS-SUS210", "suspension", "Bosch", "18750.00", 3, "Комплект усиленных рычагов с сайлентблоками для передней оси.", "4.5"),
            ("Аккумулятор VARTA Silver Dynamic AGM", "VAR-A7-70", "electrical", "VARTA", "21990.00", 3, "AGM-аккумулятор для автомобилей с системой Start-Stop и большим числом потребителей.", "4.7"),
            ("Катушка зажигания Bosch", "BOS-0221604", "electrical", "Bosch", "6340.00", 9, "Надёжная высоковольтная катушка с точными заводскими параметрами.", "4.6"),
            ("Моторное масло Castrol EDGE 5W-30, 4 л", "CAS-15B2F3", "fluids", "Castrol", "5260.00", 25, "Полностью синтетическое масло для современных бензиновых и дизельных двигателей.", "4.8"),
            ("Тормозная жидкость Brembo DOT 4, 1 л", "BRM-L04010", "fluids", "Brembo", "1480.00", 22, "Высокая температура кипения и стабильная работа тормозной системы.", "4.7"),
            ("Тормозные колодки Brembo P 85 020", "BRM-P85020", "brakes", "Brembo", "5790.00", 24, "Надёжные дисковые колодки для городского режима с низким уровнем шума.", "4.7"),
            ("Тормозные колодки Brembo Xtra P 83 133", "BRM-P83133", "brakes", "Brembo", "7960.00", 11, "Колодки серии Xtra с устойчивым коэффициентом трения при интенсивном торможении.", "4.9"),
            ("Тормозной диск Bosch QuietCast задний", "BOS-BD1814", "brakes", "Bosch", "6490.00", 17, "Задний тормозной диск с защитным покрытием и минимальным уровнем вибраций.", "4.6"),
            ("Тормозной диск Bosch вентилируемый", "BOS-BD1822", "brakes", "Bosch", "8740.00", 9, "Вентилируемый диск для эффективного охлаждения при повторных торможениях.", "4.8"),
            ("Воздушный фильтр MANN-FILTER C 25 114", "MAN-C25114", "filters", "MANN-FILTER", "1640.00", 35, "Панельный воздушный фильтр с большой площадью фильтрующего материала.", "4.7"),
            ("Воздушный фильтр MANN-FILTER C 30 130", "MAN-C30130", "filters", "MANN-FILTER", "2190.00", 28, "Фильтр тонкой очистки воздуха для стабильной работы двигателя.", "4.8"),
            ("Масляный фильтр Bosch P 7091", "BOS-P7091", "filters", "Bosch", "1180.00", 42, "Масляный фильтр с надёжным обратным клапаном и прочным корпусом.", "4.6"),
            ("Масляный фильтр Bosch P 3314", "BOS-P3314", "filters", "Bosch", "1350.00", 30, "Фильтр для качественной очистки моторного масла в широком диапазоне температур.", "4.7"),
            ("Свечи зажигания Denso Iridium IK20, 4 шт.", "DEN-IK20", "ignition", "Denso", "4680.00", 21, "Иридиевые свечи с повышенным ресурсом и устойчивым искрообразованием.", "4.9"),
            ("Свечи зажигания Denso Nickel K20TT, 4 шт.", "DEN-K20TT", "ignition", "Denso", "2480.00", 38, "Никелевые свечи Twin Tip для экономичного повседневного обслуживания.", "4.6"),
            ("Свечи зажигания NGK Iridium IX, 4 шт.", "NGK-6418", "ignition", "NGK", "5120.00", 19, "Комплект иридиевых свечей для уверенного запуска и плавного разгона.", "4.9"),
            ("Свечи зажигания NGK V-Line, 4 шт.", "NGK-1263", "ignition", "NGK", "2890.00", 33, "Свечи с V-образным центральным электродом для стабильной работы двигателя.", "4.7"),
            ("Амортизатор Bilstein B4 задний", "BIL-19103150", "suspension", "Bilstein", "9840.00", 14, "Газовый задний амортизатор с настройками, близкими к заводским.", "4.7"),
            ("Амортизатор Bilstein B8 передний", "BIL-35108788", "suspension", "Bilstein", "16900.00", 6, "Укороченный спортивный амортизатор для заниженной подвески.", "4.8"),
            ("Комплект передних рычагов Bosch", "BOS-SUS310", "suspension", "Bosch", "21400.00", 8, "Рычаги передней подвески с установленными сайлентблоками и шаровыми опорами.", "4.6"),
            ("Стойки стабилизатора Bosch, 2 шт.", "BOS-SUS115", "suspension", "Bosch", "4360.00", 26, "Комплект стоек стабилизатора для устранения люфта и посторонних шумов.", "4.7"),
            ("Аккумулятор VARTA Blue Dynamic E11", "VAR-E11-74", "electrical", "VARTA", "15490.00", 12, "Надёжный аккумулятор 74 А·ч для автомобилей со стандартным электрооборудованием.", "4.8"),
            ("Аккумулятор VARTA Black Dynamic C15", "VAR-C15-56", "electrical", "VARTA", "10990.00", 18, "Практичный аккумулятор 56 А·ч с уверенным холодным запуском.", "4.6"),
            ("Модуль зажигания Bosch", "BOS-0221503", "electrical", "Bosch", "8420.00", 10, "Высоковольтный модуль для точного управления искрой в любых режимах работы.", "4.7"),
            ("Катушка зажигания Bosch Double Spark", "BOS-0221504", "electrical", "Bosch", "7190.00", 15, "Двухискровая катушка с прочным корпусом и стабильными электрическими параметрами.", "4.8"),
        ]
        product_images = {
            "BRM-P06072": "products/brm-p06072.png",
            "BOS-BD1808": "products/bos-bd1808.png",
            "MAN-C35154": "products/man-c35154.png",
            "BOS-P3274": "products/bos-p3274.png",
            "DEN-4704": "products/den-4704.png",
            "NGK-3199": "products/ngk-3199.png",
            "BIL-24186742": "products/bil-24186742.png",
            "BOS-SUS210": "products/bos-sus210.png",
            "VAR-A7-70": "products/var-a7-70.png",
            "BOS-0221604": "products/bos-0221604.png",
            "CAS-15B2F3": "products/cas-15b2f3.png",
            "BRM-L04010": "products/brm-l04010.png",
            "BRM-P85020": "products/brm-p85020.png",
            "BRM-P83133": "products/brm-p83133.png",
            "BOS-BD1814": "products/bos-bd1814.png",
            "BOS-BD1822": "products/bos-bd1822.png",
            "MAN-C25114": "products/man-c25114.png",
            "MAN-C30130": "products/man-c30130.png",
            "BOS-P7091": "products/bos-p7091.png",
            "BOS-P3314": "products/bos-p3314.png",
            "DEN-IK20": "products/den-ik20.png",
            "DEN-K20TT": "products/den-k20tt.png",
            "NGK-6418": "products/ngk-6418.png",
            "NGK-1263": "products/ngk-1263.png",
            "BIL-19103150": "products/bil-19103150.png",
            "BIL-35108788": "products/bil-35108788.png",
            "BOS-SUS310": "products/bos-sus310.png",
            "BOS-SUS115": "products/bos-sus115.png",
            "VAR-E11-74": "products/var-e11-74.png",
            "VAR-C15-56": "products/var-c15-56.png",
            "BOS-0221503": "products/bos-0221503.png",
            "BOS-0221504": "products/bos-0221504.png",
        }
        products = []
        for name, sku, category_key, brand, price, stock, description, rating in product_data:
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={"name": name, "category": categories[category_key], "manufacturer": manufacturers[brand], "price": Decimal(price), "stock": stock, "description": description, "rating": Decimal(rating), "image": product_images[sku]},
            )
            if not product.image:
                product.image.name = product_images[sku]
                product.save(update_fields=("image",))
            products.append(product)

        baseline_time = timezone.now() - timedelta(days=60)
        StockMovement.objects.filter(product__in=products, reason=StockMovement.Reason.INITIAL).update(created_at=baseline_time)

        ProductReview.objects.update_or_create(
            product=products[0],
            user=buyer,
            defaults={"rating": 5, "text": "Колодки работают тихо, торможение стало заметно увереннее. Установились без доработок.", "admin_reply": "Спасибо за подробный отзыв! Рады, что комплект подошёл и хорошо показал себя в эксплуатации.", "replied_by": admin, "replied_at": timezone.now(), "is_published": True},
        )
        ProductReview.objects.update_or_create(
            product=products[4],
            user=buyer,
            defaults={"rating": 5, "text": "Двигатель запускается легче, комплект выглядит качественно. Посмотрим на ресурс.", "is_published": True},
        )
        ProductQuestion.objects.get_or_create(
            product=products[8],
            user=buyer,
            text="Подойдёт ли этот аккумулятор для автомобиля с системой Start-Stop?",
            defaults={"answer": "Да, это AGM-модель, рассчитанная на автомобили с системой Start-Stop. Перед заказом проверьте размеры и полярность.", "answered_by": admin, "answered_at": timezone.now(), "is_published": True},
        )
        ProductQuestion.objects.get_or_create(
            product=products[1],
            user=buyer,
            text="Диск продаётся поштучно или комплектом на ось?",
            defaults={"is_published": True},
        )

        scenarios = [
            (27, [(products[4], 2), (products[10], 1)], Order.Status.DELIVERED),
            (18, [(products[0], 1), (products[3], 2)], Order.Status.PAID),
            (9, [(products[6], 1)], Order.Status.CANCELLED),
            (2, [(products[2], 1), (products[11], 2)], Order.Status.CREATED),
        ]
        for days_ago, lines, target_status in scenarios:
            address = f"[DEMO] г. Муром, ул. Московская, д. {days_ago}"
            if Order.objects.filter(user=buyer, delivery_address=address).exists():
                continue
            try:
                for product, quantity in lines:
                    add_to_cart(buyer, product, quantity)
                order = create_order(buyer, address)
                event_time = timezone.now() - timedelta(days=days_ago)
                Order.objects.filter(pk=order.pk).update(created_at=event_time)
                StockMovement.objects.filter(order=order, reason=StockMovement.Reason.ORDER).update(created_at=event_time)
                if target_status in (Order.Status.PAID, Order.Status.DELIVERED):
                    process_payment(order, "4242424242424242")
                    paid_time = event_time + timedelta(minutes=12)
                    Order.objects.filter(pk=order.pk).update(paid_at=paid_time)
                    PaymentAttempt.objects.filter(order=order).update(created_at=paid_time)
                    order.refresh_from_db()
                    if target_status == Order.Status.DELIVERED:
                        transition_order(order, Order.Status.DELIVERED, admin)
                        Order.objects.filter(pk=order.pk).update(delivered_at=event_time + timedelta(days=3))
                elif target_status == Order.Status.CANCELLED:
                    cancel_order(order, admin)
                    StockMovement.objects.filter(order=order, reason=StockMovement.Reason.CANCELLATION).update(created_at=event_time + timedelta(hours=2))
                    Order.objects.filter(pk=order.pk).update(cancelled_at=event_time + timedelta(hours=2), restocked_at=event_time + timedelta(hours=2))
            finally:
                buyer.cart.items.all().delete()

        self.stdout.write(self.style.SUCCESS("Демонстрационные данные готовы."))
        if admin_created:
            self.stdout.write(f"Администратор: {admin.username} / пароль из DEMO_ADMIN_PASSWORD")
        else:
            password_note = "обновлён из DEMO_ADMIN_PASSWORD" if os.environ.get("DEMO_ADMIN_PASSWORD") else "существующий пароль сохранён"
            self.stdout.write(f"Администратор: {admin.username} / {password_note}")
        self.stdout.write("Покупатель: buyer / Buyer123!")
