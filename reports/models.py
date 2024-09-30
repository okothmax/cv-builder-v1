from django.db import models


class PaymentIdentification(models.Model):
    description = models.CharField(max_length=1000, blank=True, null=True)
    money_in = models.CharField(max_length=500, blank=True, null=True)
