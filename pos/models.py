from django.db import models


class Product(models.Model):

    name = models.CharField(
        max_length=100
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name


class Transaction(models.Model):

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("qr", "QR"),
    ]

    CUSTOMER_TYPES = [
        ("regular", "Regular"),
        ("sc_pwd", "SC / PWD"),
    ]

    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("voided", "Voided"),
    ]

    transaction_date = models.DateTimeField(
        auto_now_add=True
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        default="cash"
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    change = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    reference_number = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="completed"
    )

    void_reason = models.TextField(
        blank=True,
        default=""
    )

    voided_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # CUSTOMER / DISCOUNT

    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPES,
        default="regular"
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"Transaction #{self.id}"

class OrderItem(models.Model):

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    cost_subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"