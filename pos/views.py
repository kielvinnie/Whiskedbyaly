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


        # ==========================================
        # CUSTOMER TYPE
        # ==========================================

        customer_type = data.get(
            "customer_type",
            "regular"
        )

        if customer_type not in [
            "regular",
            "sc_pwd"
        ]:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid customer type."
                },
                status=400
            )


        # ==========================================
        # DISCOUNT
        # ==========================================

        if customer_type == "sc_pwd":

            discount_percentage = Decimal("20.00")

        else:

            discount_percentage = Decimal("0.00")


        # ==========================================
        # PAYMENT INFORMATION
        # ==========================================

        payment_method = data.get(
            "payment_method",
            "cash"
        )

        reference_number = data.get(
            "reference_number",
            ""
        ).strip()


        if payment_method not in [
            "cash",
            "qr"
        ]:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid payment method."
                },
                status=400
            )


        # QR requires a reference number

        if (
            payment_method == "qr"
            and not reference_number
        ):

            return JsonResponse(
                {
                    "success": False,
                    "error":
                        "QR reference number is required."
                },
                status=400
            )


        # Cash transactions don't need
        # a reference number

        if payment_method == "cash":

            reference_number = ""


        # ==========================================
        # AMOUNT PAID
        # ==========================================

        amount_paid = Decimal(
            str(
                data.get(
                    "amount_paid",
                    0
                )
            )
        )


        # ==========================================
        # CALCULATE ORIGINAL TOTAL
        # ==========================================

        original_total = Decimal("0.00")


        for item in items:

            product = Product.objects.get(
                id=item["id"],
                is_active=True
            )

            quantity = int(
                item["quantity"]
            )

            if quantity <= 0:

                return JsonResponse(
                    {
                        "success": False,
                        "error":
                            "Invalid quantity."
                    },
                    status=400
                )


            subtotal = (
                product.price *
                quantity
            )

            original_total += subtotal


        # ==========================================
        # CALCULATE DISCOUNT AMOUNT
        # ==========================================

        discount_amount = (
            original_total *
            discount_percentage /
            Decimal("100")
        )


        # ==========================================
        # FINAL TOTAL
        # ==========================================

        total = (
            original_total -
            discount_amount
        )


        # Make sure Decimal is properly rounded

        discount_amount = (
            discount_amount.quantize(
                Decimal("0.01")
            )
        )

        total = (
            total.quantize(
                Decimal("0.01")
            )
        )


        # ==========================================
        # QR PAYMENT
        # ==========================================

        if payment_method == "qr":

            # QR is considered fully paid

            amount_paid = total


        # ==========================================
        # CASH PAYMENT
        # ==========================================

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


        # ==========================================
        # CHANGE
        # ==========================================

        change = (
            amount_paid -
            total
        ).quantize(
            Decimal("0.01")
        )


        # ==========================================
        # CREATE TRANSACTION
        # ==========================================

        transaction = Transaction.objects.create(

            total=total,

            payment_method=payment_method,

            amount_paid=amount_paid,

            change=change,

            reference_number=reference_number,

            customer_type=customer_type,

            discount_percentage=discount_percentage,

            discount_amount=discount_amount

        )


        # ==========================================
        # CREATE ORDER ITEMS
        # ==========================================

        for item in items:

            product = Product.objects.get(
                id=item["id"],
                is_active=True
            )

            quantity = int(
                item["quantity"]
            )


            # Original product subtotal

            subtotal = (
                product.price *
                quantity
            )


            # Cost subtotal

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


        # ==========================================
        # SUCCESS
        # ==========================================

        return JsonResponse(
            {
                "success": True,

                "transaction_id":
                    transaction.id,

                "original_total":
                    str(original_total),

                "discount_percentage":
                    str(discount_percentage),

                "discount_amount":
                    str(discount_amount),

                "total":
                    str(total),

                "amount_paid":
                    str(amount_paid),

                "change":
                    str(change)
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


    except (ValueError, TypeError):

        return JsonResponse(
            {
                "success": False,
                "error":
                    "Invalid order information."
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


# ==================================================
# SALES
# ==================================================

def sales(request):

    today = timezone.localdate()

    # ==========================================
    # COMPLETED TRANSACTIONS ONLY
    # ==========================================

    transactions = (
        Transaction.objects
        .filter(
            status="completed"
        )
        .prefetch_related(
            "items__product"
        )
        .order_by(
            "-transaction_date"
        )
    )

    # ==========================================
    # TODAY'S TRANSACTIONS
    # ==========================================

    today_transactions = (
        transactions.filter(
            transaction_date__date=today
        )
    )

    # ==========================================
    # TODAY'S TOTAL SALES
    # ==========================================

    today_total = (
        today_transactions.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # TODAY'S CASH SALES
    # ==========================================

    cash_total = (
        today_transactions
        .filter(
            payment_method="cash"
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # TODAY'S QR SALES
    # ==========================================

    qr_total = (
        today_transactions
        .filter(
            payment_method="qr"
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # CONTEXT
    # ==========================================

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

# ==================================================
# DASHBOARD
# ==================================================

def dashboard(request):

    # ==========================================
    # OVERALL BUSINESS DATA — ALL TIME
    # ==========================================

    overall_total_sales = (
        Transaction.objects.filter(
            status="completed"
        ).aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )


    overall_total_cost = (
        OrderItem.objects.filter(
            transaction__status="completed"
        ).aggregate(
            total=Sum("cost_subtotal")
        )["total"]
        or Decimal("0.00")
    )


    overall_net_profit = (
        overall_total_sales -
        overall_total_cost
    )


    overall_transactions_count = (
        Transaction.objects.filter(
            status="completed"
        ).count()
    )


    overall_products_sold = (
        OrderItem.objects.filter(
            transaction__status="completed"
        ).aggregate(
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
        .filter(
            transaction__status="completed"
        )
        .values(
            "product__name"
        )
        .annotate(
            total_quantity=Sum(
                "quantity"
            )
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
    # START WITH COMPLETED TRANSACTIONS ONLY
    # ==========================================

    filtered_transactions = (
        Transaction.objects
        .filter(
            status="completed"
        )
        .prefetch_related(
            "items__product"
        )
        .order_by(
            "-transaction_date"
        )
    )


    # ==========================================
    # FILTER BY DATE
    # ==========================================

    if (
        period == "day"
        and selected_date
    ):

        filtered_transactions = (
            filtered_transactions.filter(
                transaction_date__date=
                    selected_date
            )
        )


    # ==========================================
    # FILTER BY MONTH
    # ==========================================

    elif (
        period == "month"
        and selected_month
    ):

        try:

            year, month = (
                selected_month.split("-")
            )

            filtered_transactions = (
                filtered_transactions.filter(
                    transaction_date__year=
                        int(year),

                    transaction_date__month=
                        int(month)
                )
            )

        except (
            ValueError,
            TypeError
        ):

            pass


    # ==========================================
    # FILTER BY YEAR
    # ==========================================

    elif (
        period == "year"
        and selected_year
    ):

        try:

            filtered_transactions = (
                filtered_transactions.filter(
                    transaction_date__year=
                        int(selected_year)
                )
            )

        except (
            ValueError,
            TypeError
        ):

            pass


    # ==========================================
    # SELECTED PERIOD SALES
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

    filtered_items = (
        OrderItem.objects.filter(
            transaction__in=
                filtered_transactions
        )
    )


    # ==========================================
    # SELECTED PERIOD COST
    # ==========================================

    filtered_total_cost = (
        filtered_items.aggregate(
            total=Sum(
                "cost_subtotal"
            )
        )["total"]
        or Decimal("0.00")
    )


    # ==========================================
    # SELECTED PERIOD PROFIT
    # ==========================================

    filtered_net_profit = (
        filtered_total_sales -
        filtered_total_cost
    )


    # ==========================================
    # TRANSACTION COUNT
    # ==========================================

    filtered_transactions_count = (
        filtered_transactions.count()
    )


    # ==========================================
    # BEST SELLER
    # ==========================================

    filtered_best_seller = (
        filtered_items
        .values(
            "product__name"
        )
        .annotate(
            total_quantity=
                Sum("quantity")
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

# ==================================================
# VOID ORDER
# ==================================================

def void_transaction(request, transaction_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request method."
            },
            status=405
        )

    try:

        transaction = Transaction.objects.get(
            id=transaction_id
        )

        data = json.loads(request.body)

        reason = data.get(
            "reason",
            ""
        ).strip()

        # Delete the transaction.
        # OrderItem records are also deleted automatically
        # because transaction uses on_delete=models.CASCADE.
        transaction.delete()

        return JsonResponse(
            {
                "success": True,
                "message": "Transaction voided and removed successfully.",
                "transaction_id": transaction_id
            }
        )

    except Transaction.DoesNotExist:

        return JsonResponse(
            {
                "success": False,
                "error": "Transaction not found."
            },
            status=404
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request data."
            },
            status=400
        )

    except Exception as e:

        print(
            "VOID TRANSACTION ERROR:",
            e
        )

        return JsonResponse(
            {
                "success": False,
                "error": "Unable to void this transaction."
            },
            status=500
        )