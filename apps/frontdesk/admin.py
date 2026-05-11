from django.contrib import admin
from .models import PaymentRecord, CashRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'payment_date', 'amount', 'project',
                    'payment_type', 'payer_type', 'insurance_claimed', 'invoiced']
    list_filter = ['payment_type', 'payer_type', 'payment_date', 'insurance_claimed']
    search_fields = ['customer_name', 'transaction_ref', 'project']


@admin.register(CashRecord)
class CashRecordAdmin(admin.ModelAdmin):
    list_display = ['record_date', 'type', 'amount', 'description', 'payee']
    list_filter = ['type', 'category']
    search_fields = ['description', 'payee']
