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

            # Calculate the total cost
            # for this product in this order

            cost_subtotal = (
                product.cost *
                quantity
            )


            OrderItem.objects.create(

                transaction=transaction,

                product=product,

                quantity=quantity,

                price=product.price,

                cost=product.cost,

                subtotal=subtotal,

                cost_subtotal=cost_subtotal

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
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    qr_total = (
        today_transactions
        .filter(payment_method="qr")
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    context = {

        "transactions":
            transactions,

        "today_total":
            today_total,

        "today_transactions_count":
            today_transactions.count(),

        "cash_total":
            cash_total,

        "qr_total":
            qr_total,

        "today":
            today,

    }

    return render(
        request,
        "pos/sales.html",
        context
    )


def dashboard(request):

    # ==========================================
    # OVERALL BUSINESS DATA — ALL TIME
    # ==========================================

    overall_total_sales = (
        Transaction.objects.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    overall_total_cost = (
        OrderItem.objects.aggregate(
            total=Sum("cost_subtotal")
        )["total"]
        or Decimal("0.00")
    )

    overall_net_profit = (
        overall_total_sales
        - overall_total_cost
    )

    overall_transactions_count = (
        Transaction.objects.count()
    )

    overall_products_sold = (
        OrderItem.objects.aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )

    total_products = (
        Product.objects.filter(
            is_active=True
        ).count()
    )


    # ==========================================
    # OVERALL BEST SELLER
    # ==========================================

    overall_best_seller = (
        OrderItem.objects
        .values(
            "product__name"
        )
        .annotate(
            total_quantity=Sum("quantity")
        )
        .order_by(
            "-total_quantity"
        )
        .first()
    )


    # ==========================================
    # SALES ANALYSIS FILTER
    # ==========================================

    period = request.GET.get(
        "period",
        "day"
    )

    selected_date = request.GET.get(
        "date"
    )

    selected_month = request.GET.get(
        "month"
    )

    selected_year = request.GET.get(
        "year"
    )


    # ==========================================
    # START WITH ALL TRANSACTIONS
    # ==========================================

    filtered_transactions = (
        Transaction.objects
        .prefetch_related("items__product")
        .order_by("-transaction_date")
    )


    # ==========================================
    # FILTER BY DATE
    # ==========================================

    if period == "day" and selected_date:

        filtered_transactions = (
            filtered_transactions.filter(
                transaction_date__date=selected_date
            )
        )


    # ==========================================
    # FILTER BY MONTH
    # ==========================================

    elif period == "month" and selected_month:

        try:

            year, month = selected_month.split("-")

            filtered_transactions = (
                filtered_transactions.filter(
                    transaction_date__year=int(year),
                    transaction_date__month=int(month)
                )
            )

        except (ValueError, TypeError):

            pass


    # ==========================================
    # FILTER BY YEAR
    # ==========================================

    elif period == "year" and selected_year:

        try:

            filtered_transactions = (
                filtered_transactions.filter(
                    transaction_date__year=int(
                        selected_year
                    )
                )
            )

        except (ValueError, TypeError):

            pass


    # ==========================================
    # SELECTED PERIOD TOTAL SALES
    # ==========================================

    filtered_total_sales = (
        filtered_transactions.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )


    # ==========================================
    # SELECTED PERIOD ITEMS
    # ==========================================

    filtered_items = OrderItem.objects.filter(
        transaction__in=filtered_transactions
    )


    # ==========================================
    # SELECTED PERIOD TOTAL COST
    # ==========================================

    filtered_total_cost = (
        filtered_items.aggregate(
            total=Sum("cost_subtotal")
        )["total"]
        or Decimal("0.00")
    )


    # ==========================================
    # SELECTED PERIOD NET PROFIT
    # ==========================================

    filtered_net_profit = (
        filtered_total_sales
        - filtered_total_cost
    )


    # ==========================================
    # SELECTED PERIOD TRANSACTION COUNT
    # ==========================================

    filtered_transactions_count = (
        filtered_transactions.count()
    )


    # ==========================================
    # SELECTED PERIOD BEST SELLER
    # ==========================================

    filtered_best_seller = (
        filtered_items
        .values(
            "product__name"
        )
        .annotate(
            total_quantity=Sum("quantity")
        )
        .order_by(
            "-total_quantity"
        )
        .first()
    )


    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        # --------------------------------------
        # Overall
        # --------------------------------------

        "overall_total_sales":
            overall_total_sales,

        "overall_total_cost":
            overall_total_cost,

        "overall_net_profit":
            overall_net_profit,

        "overall_transactions_count":
            overall_transactions_count,

        "overall_products_sold":
            overall_products_sold,

        "total_products":
            total_products,

        "overall_best_seller":
            overall_best_seller,


        # --------------------------------------
        # Filtered
        # --------------------------------------

        "filtered_total_sales":
            filtered_total_sales,

        "filtered_total_cost":
            filtered_total_cost,

        "filtered_net_profit":
            filtered_net_profit,

        "filtered_transactions_count":
            filtered_transactions_count,

        "filtered_best_seller":
            filtered_best_seller,

        "filtered_transactions":
            filtered_transactions,


        # --------------------------------------
        # Filter values
        # --------------------------------------

        "period":
            period,

        "selected_date":
            selected_date,

        "selected_month":
            selected_month,

        "selected_year":
            selected_year,

    }


    return render(
        request,
        "pos/dashboard.html",
        context
    )