from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def employer_required(function=None, redirect_field_name=None, login_url='users:login'):
    """
    Decorator for views that checks that the user is logged in and is an employer.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_employer,
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def customer_required(function=None, redirect_field_name=None, login_url='users:login'):
    """
    Decorator for views that checks that the user is logged in and is a customer.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_customer,
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
