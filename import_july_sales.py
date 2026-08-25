import os
import django
from datetime import datetime
from decimal import Decimal

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "matchapos.settings"
)

django.setup()

from pos.models import Product, Transaction, OrderItem


# =========================================================
# JULY 2026 HISTORICAL SALES
# All treated as CASH
# All treated as July 31, 2026
# =========================================================

sales = [

    # order, sales price, cost
    ("Matcha Flight", Decimal("0.00"), Decimal("492.70")),

    ("Matcha Flight", Decimal("600.00"), Decimal("492.70")),

    ("Matcha Flight", Decimal("0.00"), Decimal("492.70")),

    ("Chocnut Matcha", Decimal("220.00"), Decimal("117.73")),

    ("Matcha Flight", Decimal("0.00"), Decimal("492.70")),

    ("Matcha Flight", Decimal("1000.00"), Decimal("492.70")),

    ("Chocnut Matcha", Decimal("220.00"), Decimal("117.73")),

    (
        "Chocnut Matcha with Chocnut Hojicha",
        Decimal("300.00"),
        Decimal("117.73")
    ),

    (
        "Matcha Flight with Matcha Blanca",
        Decimal("600.00"),
        Decimal("492.70")
    ),

    ("Matcha Flight", Decimal("600.00"), Decimal("492.70")),

    ("Matcha Flight", Decimal("600.00"), Decimal("492.70")),

    ("Matcha Flight", Decimal("0.00"), Decimal("492.70")),

    ("Chocnut Matcha", Decimal("250.00"), Decimal("117.73")),

    ("Yema Matcha", Decimal("250.00"), Decimal("105.73")),

    ("Matcha Oat Latte", Decimal("250.00"), Decimal("121.73")),

    ("Matcha Oat Latte", Decimal("250.00"), Decimal("121.73")),

    ("Pastillas Matcha", Decimal("250.00"), Decimal("117.73")),

    ("Mais Con Yelo Matcha", Decimal("250.00"), Decimal("123.39")),

    ("Yema Matcha", Decimal("250.00"), Decimal("105.73")),

    ("Chocnut Matcha", Decimal("0.00"), Decimal("117.73")),
]


# =========================================================
# JULY DATE
# =========================================================

july_date = datetime(
    2026,
    7,
    31,
    12,
    0,
    0
)


# =========================================================
# PREVENT DUPLICATE IMPORT
# =========================================================

reference = "JULY-2026-HISTORICAL"

existing = Transaction.objects.filter(
    reference_number=reference
)

if existing.exists():

    print()
    print("=" * 50)
    print("JULY SALES ALREADY IMPORTED")
    print("=" * 50)

    print(
        f"Existing transactions: {existing.count()}"
    )

    print(
        "Nothing was added."
    )

    print("=" * 50)

    raise SystemExit


# =========================================================
# CREATE SALES
# =========================================================

created_count = 0

total_sales = Decimal("0.00")

total_cost = Decimal("0.00")


for product_name, sale_price, unit_cost in sales:

    # -----------------------------------------
    # Find or create product
    # -----------------------------------------

    product = Product.objects.filter(
        name=product_name
    ).first()


    if product is None:

        product = Product.objects.create(

            name=product_name,

            price=sale_price,

            cost=unit_cost,

            is_active=True

        )

        print(
            f"Created product: {product_name}"
        )


    else:

        # Update product cost so Admin
        # reflects the historical cost.

        product.cost = unit_cost

        product.save(
            update_fields=["cost"]
        )


    # -----------------------------------------
    # Create transaction
    # -----------------------------------------

    transaction = Transaction.objects.create(

        total=sale_price,

        payment_method="cash",

        amount_paid=sale_price,

        change=Decimal("0.00"),

        reference_number=reference

    )


    # -----------------------------------------
    # Set transaction date to July 31
    # -----------------------------------------

    Transaction.objects.filter(
        id=transaction.id
    ).update(
        transaction_date=july_date
    )


    # -----------------------------------------
    # Create order item
    # -----------------------------------------

    cost_subtotal = (
        unit_cost * Decimal("1")
    )


    OrderItem.objects.create(

        transaction=transaction,

        product=product,

        quantity=1,

        price=sale_price,

        cost=unit_cost,

        subtotal=sale_price,

        cost_subtotal=cost_subtotal

    )


    created_count += 1

    total_sales += sale_price

    total_cost += cost_subtotal


# =========================================================
# FINAL CALCULATION
# =========================================================

net_profit = (
    total_sales
    - total_cost
)


# =========================================================
# DONE
# =========================================================

print()

print("=" * 55)

print("JULY SALES IMPORT COMPLETE")

print("=" * 55)

print(
    f"Transactions created: {created_count}"
)

print(
    f"Total sales:          ₱{total_sales:,.2f}"
)

print(
    f"Total cost:           ₱{total_cost:,.2f}"
)

print(
    f"Calculated net profit: ₱{net_profit:,.2f}"
)

print(
    "Date: July 31, 2026"
)

print(
    "Payment: Cash"
)

print("=" * 55)