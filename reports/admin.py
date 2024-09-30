from django.contrib import admin
from .models import PaymentIdentification
from import_export.admin import ImportExportModelAdmin


@admin.register(PaymentIdentification)
class PaymentIdentificationAdmin(ImportExportModelAdmin):
    list_display = ('description', 'money_in')
    search_fields = ('description', 'money_in')
    list_per_page = 10
