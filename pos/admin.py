from django.contrib import admin
from .models import Product, Transaction, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "price",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "transaction_date",
        "total",
        "amount_paid",
        "change",
    )

    list_display_links = (
        "id",
    )

    ordering = (
        "-transaction_date",
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "transaction",
        "product",
        "quantity",
        "price",
        "subtotal",
    )

    list_filter = (
        "product",
    )

    search_fields = (
        "product__name",
    )
    