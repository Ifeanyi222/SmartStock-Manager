# sales_record/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def manager_required(view_func):
    def check_manager(user):
        return hasattr(user, 'profile') and user.profile.role == 'manager'

    decorator = user_passes_test(check_manager, login_url='login')
    
    def _wrapped_view(request, *args, **kwargs):
        if not check_manager(request.user):
            messages.error(request, "🚫 Access denied. Manager only area.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return decorator(_wrapped_view)
