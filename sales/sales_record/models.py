from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Product(models.Model):
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    ref_no = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    supplier = models.CharField(max_length=100, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    condition = models.CharField(
        max_length=50,
        choices=[('new', 'New'), ('used', 'Used')],
        default='new'
    )
    quantity = models.BigIntegerField(default=0)
    selling_price = models.DecimalField(max_digits=20, decimal_places=2)
    remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.brand} - {self.model_name}"

    @property
    def is_low_stock(self):
        return self.quantity <= 10


class Sale(models.Model):
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    def __str__(self):
        return f"Sale #{self.id} - {self.date.strftime('%Y-%m-%d')}"

    def calculate_total(self):
        total = sum(item.subtotal() for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=2)
    remark = models.CharField(max_length=255, blank=True, null=True)

    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product.brand} - {self.quantity} pcs"


@receiver(post_save, sender=SaleItem)
def update_product_stock(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        if instance.quantity > product.quantity:
            raise ValueError(f"Not enough stock for {product.brand} - {product.model_name}")
        product.quantity -= instance.quantity
        product.save()
