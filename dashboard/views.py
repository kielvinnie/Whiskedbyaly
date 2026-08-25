from decimal import Decimal

from django.shortcuts import render
from django.db.models import Sum

from pos.models import Product, Transaction, OrderItem


def home(request):

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
        .values("product__name")
        .annotate(
            total_quantity=Sum("quantity")
        )
        .order_by("-total_quantity")
        .first()
    )

    # ==========================================
    # SALES ANALYSIS
    # ==========================================

    period = request.GET.get(
        "period",
        "day"
    )

    selected_date = request.GET.get(
        "date",
        ""
    )

    selected_month = request.GET.get(
        "month",
        ""
    )

    selected_year = request.GET.get(
        "year",
        ""
    )

    filtered_transactions = (
        Transaction.objects
        .prefetch_related("items__product")
        .order_by("-transaction_date")
    )

    # ==========================================
    # DATE FILTER
    # ==========================================

    if period == "day" and selected_date:

        filtered_transactions = (
            filtered_transactions.filter(
                transaction_date__date=selected_date
            )
        )

    # ==========================================
    # MONTH FILTER
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
    # YEAR FILTER
    # ==========================================

    elif period == "year" and selected_year:

        try:

            filtered_transactions = (
                filtered_transactions.filter(
                    transaction_date__year=int(selected_year)
                )
            )

        except (ValueError, TypeError):

            pass

    # ==========================================
    # FILTERED SALES
    # ==========================================

    filtered_total_sales = (
        filtered_transactions.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # FILTERED COST
    # ==========================================

    filtered_items = OrderItem.objects.filter(
        transaction__in=filtered_transactions
    )

    filtered_total_cost = (
        filtered_items.aggregate(
            total=Sum("cost_subtotal")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # FILTERED NET PROFIT
    # ==========================================

    filtered_net_profit = (
        filtered_total_sales
        - filtered_total_cost
    )

    # ==========================================
    # FILTERED TRANSACTION COUNT
    # ==========================================

    filtered_transactions_count = (
        filtered_transactions.count()
    )

    # ==========================================
    # FILTERED BEST SELLER
    # ==========================================

    filtered_best_seller = (
        filtered_items
        .values("product__name")
        .annotate(
            total_quantity=Sum("quantity")
        )
        .order_by("-total_quantity")
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
        # Selected Period
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
        # Filters
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
        "dashboard/home.html",
        context
    )