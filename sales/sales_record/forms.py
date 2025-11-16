from django import forms
from django.forms import inlineformset_factory
from .models import Sale, SaleItem, Product


# 🧾 SALE FORM
class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer_name', 'payment_method']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer name (optional)'
            }),
            'payment_method': forms.Select(choices=[
                ('Cash', 'Cash'),
                ('Transfer', 'Transfer'),
                ('POS', 'POS'),
                ('Credit', 'Credit'),
            ], attrs={'class': 'form-select'}),
        }


# 🛠️ SALE ITEM FORM
class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'min': 1
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            if quantity > product.quantity:
                raise forms.ValidationError(
                    f"⚠️ Not enough stock for {product.brand} - {product.model_name}. "
                    f"Available: {product.quantity}."
                )

        return cleaned_data


# 🧩 INLINE FORMSET: multiple SaleItems per Sale
SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=3,          # show 3 item forms by default
    can_delete=True,  # allow removing item lines
)
