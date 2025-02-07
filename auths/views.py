from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegistrationForm, CustomAuthForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # 如果用户已登录，则直接跳转到主页
    if request.method == "POST":
        username = request.POST.get('user')
        email = request.POST.get('email')
        password = request.POST.get('pass')

        # Basic validation
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'auths/login.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, 'auths/login.html')

        # Create new user
        user = User(username=username, email=email, password=make_password(password))
        user.save()
        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'auths/login.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # 如果用户已登录，则直接跳转到主页
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Basic validation
        if not username or not password:
            messages.error(request, "Please fill out all fields.")
            return render(request, 'auths/login.html')

        # Authenticate user
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'auths/login.html')

@login_required
def home_view(request):
    """登录后的主页视图"""
    return render(request, 'auths/home.html', {'user': request.user})
@login_required
def logout_view(request):
    """用户登出视图"""
    logout(request)
    messages.success(request, "您已成功登出")
    return redirect('login')
