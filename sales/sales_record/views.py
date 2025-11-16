from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from .decorators import manager_required
from .models import Product, Sale, SaleItem, Profile
from .forms import SaleForm, SaleItemFormSet


# ✅ Helper functions
def is_manager(user):
    return hasattr(user, 'profile') and user.profile.role == 'manager'

def is_staff_or_manager(user):
    return hasattr(user, 'profile') and user.profile.role in ['staff', 'manager']


# 🏠 DASHBOARD
@login_required
@user_passes_test(is_staff_or_manager)
def dashboard(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all()
    sales = Sale.objects.prefetch_related("items__product", "user").order_by("-date")[:10]

    # 🔍 Search (brand, model, ref_no, supplier, category)
    if query:
        products = products.filter(
            Q(brand__icontains=query) |
            Q(model_name__icontains=query) |
            Q(ref_no__icontains=query) |
            Q(supplier__icontains=query) |
            Q(category__icontains=query)
        )
        sales = sales.filter(items__product__brand__icontains=query).distinct()

    low_stock_products = products.filter(quantity__lt=5)

    context = {
        "products": products,
        "sales": sales,
        "low_stock_products": low_stock_products,
        "query": query,
        "role": request.user.profile.role,
    }
    return render(request, "sales_record/dashboard.html", context)


# 🔍 AJAX SEARCH (Dynamic dashboard updates)
@login_required
@user_passes_test(is_staff_or_manager)
def search_dashboard(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.all()
    sales = Sale.objects.prefetch_related("items__product", "user").order_by("-date")[:10]

    if query:
        products = products.filter(
            Q(brand__icontains=query) |
            Q(model_name__icontains=query) |
            Q(ref_no__icontains=query) |
            Q(supplier__icontains=query)
        )
        sales = sales.filter(items__product__brand__icontains=query).distinct()

    html = render_to_string("sales_record/partials/dashboard_tables.html", {
        "products": products,
        "sales": sales,
        "role": request.user.profile.role
    })

    return JsonResponse({"html": html})


# ➕ ADD STOCK
@login_required
@user_passes_test(is_manager)
def add_stock(request):
    if request.method == "POST":
        brand = request.POST.get("brand")
        model_name = request.POST.get("model_name")
        ref_no = request.POST.get("ref_no")
        category = request.POST.get("category", "")
        supplier = request.POST.get("supplier", "")
        purchase_price = request.POST.get("purchase_price") or 0
        selling_price = request.POST.get("selling_price") or 0
        quantity = int(request.POST.get("quantity", 0))
        remark = request.POST.get("remark", "")

        Product.objects.create(
            brand=brand,
            model_name=model_name,
            ref_no=ref_no,
            category=category,
            supplier=supplier,
            purchase_price=purchase_price,
            selling_price=selling_price,
            quantity=quantity,
            remark=remark,
        )

        messages.success(request, f"✅ Stock added successfully for {brand} - {model_name}.")
        return redirect("dashboard")

    return render(request, "sales_record/add_stock.html")


# 💰 RECORD SALE
@login_required
@transaction.atomic
def record_sale(request):
    if request.method == 'POST':
        sale_form = SaleForm(request.POST)

        if sale_form.is_valid():
            sale = sale_form.save(commit=False)
            sale.user = request.user
            sale.save()

            formset = SaleItemFormSet(request.POST, instance=sale)

            if formset.is_valid():
                total_amount = 0
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        item = form.save(commit=False)
                        item.price = item.product.selling_price
                        item.save()

                        # Deduct from inventory
                        product = item.product
                        if product.quantity >= item.quantity:
                            product.quantity -= item.quantity
                            product.save()
                        else:
                            messages.error(request, f"Not enough stock for {product.model_name}")
                            raise ValueError("Insufficient stock")

                        total_amount += item.subtotal()

                sale.total_amount = total_amount
                sale.save()

                messages.success(request, "✅ Sale recorded successfully!")
                return redirect('dashboard')
            else:
                messages.error(request, "⚠️ Please fix the item form errors below.")
        else:
            formset = SaleItemFormSet(request.POST)
            messages.error(request, "⚠️ Please fix the sale form errors below.")
    else:
        sale_form = SaleForm()
        formset = SaleItemFormSet()

    return render(request, 'sales_record/record_sale.html', {
        'sale_form': sale_form,
        'formset': formset,
    })


# ✏️ EDIT STOCK
@login_required
@user_passes_test(is_manager)
def edit_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.brand = request.POST.get("brand")
        product.model_name = request.POST.get("model_name")
        product.ref_no = request.POST.get("ref_no")
        product.category = request.POST.get("category")
        product.supplier = request.POST.get("supplier")
        product.purchase_price = request.POST.get("purchase_price") or 0
        product.selling_price = request.POST.get("selling_price") or 0
        product.quantity = int(request.POST.get("quantity", 0))
        product.remark = request.POST.get("remark", "")
        product.save()

        messages.success(request, "✅ Stock updated successfully.")
        return redirect("dashboard")

    return render(request, "sales_record/edit_stock.html", {"product": product})


# 🗑️ DELETE STOCK
@login_required
@user_passes_test(is_manager)
def delete_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, f"🗑️ {product.brand} - {product.model_name} deleted successfully.")
        return redirect("dashboard")

    return render(request, "sales_record/delete_stock.html", {"product": product})


# 👥 REGISTER USER
@login_required
@manager_required
def register_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role", "staff")

        if password != confirm_password:
            messages.error(request, "❌ Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already exists.")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password)
        user.profile.role = role
        user.profile.save()

        messages.success(request, f"✅ {role.capitalize()} account created successfully for {username}!")
        return redirect("dashboard")

    return render(request, "sales_record/register.html")


# 🔑 LOGIN USER
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            if not hasattr(user, "profile"):
                Profile.objects.create(user=user, role="manager" if user.is_superuser else "staff")
            login(request, user)
            messages.success(request, f"👋 Welcome back, {user.username}!")
            return redirect("dashboard")
        else:
            messages.error(request, "❌ Invalid username or password.")
            return redirect("login")
    return render(request, "sales_record/login.html")


# 🚪 LOGOUT USER
@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "👋 You have been logged out.")
    return redirect("login")


# 🧾 VIEW SALE RECEIPT
@login_required
@user_passes_test(is_staff_or_manager)
def view_sale(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related("items__product", "user"), id=sale_id)
    return render(request, "sales_record/receipt.html", {"sale": sale})
