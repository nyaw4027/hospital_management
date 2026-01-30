from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import User, Profile
from .forms import UserRegistrationForm, UserLoginForm

def home(request):
    """Home page view"""
    return render(request, 'accounts/home.html')

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create profile for user
            Profile.objects.create(user=user)
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard_redirect(request):
    """Redirect users to their role-specific dashboard"""
    user = request.user
    role = user.role.lower() if user.role else None

    if role == 'doctor':
        return redirect('doctor_dashboard')

    elif role == 'patient':
        return redirect('patient_dashboard')

    elif role == 'cashier':
        return redirect('cashier_dashboard')

    elif role == 'manager':
        return redirect('manager_dashboard')

    elif role == 'staff':
        return redirect('staff_dashboard')

    else:
        messages.warning(
            request,
            'Your account role is not set. Please contact administrator.'
        )
        return redirect('home')


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'accounts/profile.html')