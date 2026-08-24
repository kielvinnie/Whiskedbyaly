from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from decimal import Decimal
import json

from .models import Product, Transaction, OrderItem
from django.db.models import Sum
from django.utils import timezone


@ensure_csrf_cookie
def pos_home(request):

    products = Product.objects.filter(
        is_active=True
    ).order_by("name")

    return render(
        request,
        "pos/home.html",
        {
            "products": products
        }
    )


def checkout(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request method."
            },
            status=405
        )

    try:

        data = json.loads(request.body)

        items = data.get("items", [])

        if not items:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No items in order."
                },
                status=400
            )


        # ---------------------------------
        # PAYMENT INFORMATION
        # ---------------------------------

        payment_method = data.get(
            "payment_method",
            "cash"
        )

        reference_number = data.get(
            "reference_number",
            ""
        ).strip()


        if payment_method not in ["cash", "qr"]:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid payment method."
                },
                status=400
            )


        # QR requires a reference number

        if payment_method == "qr" and not reference_number:

            return JsonResponse(
                {
                    "success": False,
                    "error":
                        "QR reference number is required."
                },
                status=400
            )


        # Cash transactions don't need a reference number

        if payment_method == "cash":

            reference_number = ""


        # ---------------------------------
        # AMOUNT PAID
        # ---------------------------------

        amount_paid = Decimal(
            str(data.get("amount_paid", 0))
        )


        # ---------------------------------
        # CALCULATE TOTAL FROM DATABASE
        # ---------------------------------

        total = Decimal("0.00")


        for item in items:

            product = Product.objects.get(
                id=item["id"],
                is_active=True
            )

            quantity = int(
                item["quantity"]
            )

            subtotal = (
                product.price *
                quantity
            )

            total += subtotal


        # ---------------------------------
        # QR PAYMENT
        # ---------------------------------

        if payment_method == "qr":

            # QR is considered fully paid

            amount_paid = total


        # ---------------------------------
        # CASH PAYMENT
        # ---------------------------------

        if payment_method == "cash":

            if amount_paid < total:

                return JsonResponse(
                    {
                        "success": False,
                        "error":
                            "Insufficient payment."
                    },
                    status=400
                )


        # ---------------------------------
        # CHANGE
        # ---------------------------------

        change = amount_paid - total


        # ---------------------------------
        # CREATE TRANSACTION
        # ---------------------------------

        transaction = Transaction.objects.create(

            total=total,

            payment_method=payment_method,

            amount_paid=amount_paid,

            change=change,

            reference_number=reference_number

        )


        # ---------------------------------
        # CREATE ORDER ITEMS
        # ---------------------------------

        for item in items:

            product = Product.objects.get(
                id=item["id"],
                is_active=True
            )

            quantity = int(
                item["quantity"]
            )

            subtotal = (
                product.price *
                quantity
            )


            OrderItem.objects.create(

                transaction=transaction,

                product=product,

                quantity=quantity,

                price=product.price,

                subtotal=subtotal

            )


        # ---------------------------------
        # SUCCESS
        # ---------------------------------

        return JsonResponse(
            {
                "success": True,
                "transaction_id":
                    transaction.id
            }
        )


    except Product.DoesNotExist:

        return JsonResponse(
            {
                "success": False,
                "error":
                    "One of the products no longer exists."
            },
            status=400
        )


    except Exception as e:

        print(
            "CHECKOUT ERROR:",
            e
        )

        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=500
        )

def sales(request):

    today = timezone.localdate()

    transactions = (
        Transaction.objects
        .prefetch_related("items__product")
        .order_by("-transaction_date")
    )

    today_transactions = transactions.filter(
        transaction_date__date=today
    )

    today_total = (
        today_transactions.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    cash_total = (
        today_transactions
        .filter(payment_method="cash")
        .aggregate(total=Sum("total"))["total"]
        or Decimal("0.00")
    )

    qr_total = (
        today_transactions
        .filter(payment_method="qr")
        .aggregate(total=Sum("total"))["total"]
        or Decimal("0.00")
    )

    context = {
        "transactions": transactions,
        "today_total": today_total,
        "today_transactions_count": today_transactions.count(),
        "cash_total": cash_total,
        "qr_total": qr_total,
        "today": today,
    }

    return render(
        request,
        "pos/sales.html",
        context
    )