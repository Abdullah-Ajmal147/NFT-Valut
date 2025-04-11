from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def email_verified_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_email_verified:
            messages.warning(request, 'Please verify your email to access this feature.')
            return redirect('users:profile')
        return view_func(request, *args, **kwargs)
    return wrapper 