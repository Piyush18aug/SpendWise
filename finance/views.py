from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, TransactionForm, GoalForm, UserUpdateForm, UserProfileForm
from .models import Transaction, Goal, UserProfile
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import io

def send_welcome_email(user):
    subject = 'Welcome to SpendWise!'
    message = f'Hi {user.username},\n\nWelcome to SpendWise! Your account has been successfully created. We are excited to have you on board to manage your finances better.\n\nBest regards,\nThe SpendWise Team'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, email_from, recipient_list, fail_silently=False)

@login_required
def send_summary_email(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:10]
    total_income = sum(t.amount for t in transactions if t.type == 'Income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'Expense')
    balance = total_income - total_expenses

    subject = f'Your Financial Summary - {request.user.username}'
    context = {
        'user': request.user,
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'currency_symbol': request.user.profile.currency_symbol
    }
    
    html_message = render_to_string('emails/financial_summary.html', context)
    
    email = EmailMessage(
        subject,
        'Please view the attached summary.',
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
    )
    email.content_subtype = "html"
    email.body = html_message
    
    try:
        email.send(fail_silently=False)
        messages.success(request, 'Financial summary sent to your email!')
    except Exception as e:
        messages.warning(request, 'Successfully generated summary, but there was an issue sending the email. Please check your SendGrid configuration.')
        
    return redirect('dashboard')

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'profile.html', context)

@login_required
def settings_view(request):
    # For now, settings mostly relates to the profile preferences (like currency)
    # But we can expand it later.
    if request.method == 'POST':
        p_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if p_form.is_valid():
            p_form.save()
            messages.success(request, 'Settings updated!')
            return redirect('settings')
    else:
        p_form = UserProfileForm(instance=request.user.profile)

    return render(request, 'settings.html', {'p_form': p_form})

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def test_view(request):
    return HttpResponse("Hello World")

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            send_welcome_email(user)
            messages.success(request, 'Registration successful. You can now login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})
    # return HttpResponse("Login Page Debug")

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    
    total_income = sum(t.amount for t in transactions if t.type == 'Income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'Expense')
    balance = total_income - total_expenses
    
    # Data for charts
    income_vs_expense_labels = ['Income', 'Expense']
    income_vs_expense_data = [float(total_income), float(total_expenses)]
    
    # Category-wise expenses
    expense_categories = {}
    for t in transactions:
        if t.type == 'Expense':
            if t.category in expense_categories:
                expense_categories[t.category] += float(t.amount)
            else:
                expense_categories[t.category] = float(t.amount)
    
    category_labels = list(expense_categories.keys())
    category_data = list(expense_categories.values())
    
    context = {
        'transactions': transactions.order_by('-date'),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'income_vs_expense_labels': income_vs_expense_labels,
        'income_vs_expense_data': income_vs_expense_data,
        'category_labels': category_labels,
        'category_data': category_data,
    }
    return render(request, 'dashboard.html', context)

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'transactions/list.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'transactions/add.html', {'form': form})

@login_required
def edit_transaction(request, pk):
    try:
        transaction = Transaction.objects.get(pk=pk, user=request.user)
    except Transaction.DoesNotExist:
        return redirect('transaction_list')
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'transactions/edit.html', {'form': form})

@login_required
def delete_transaction(request, pk):
    try:
        transaction = Transaction.objects.get(pk=pk, user=request.user)
        if request.method == 'POST':
            transaction.delete()
            messages.success(request, 'Transaction deleted successfully.')
            return redirect('transaction_list')
    except Transaction.DoesNotExist:
        pass
    return redirect('transaction_list')

@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user)
    return render(request, 'goals/list.html', {'goals': goals})

@login_required
def add_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal added successfully.')
            return redirect('goal_list')
    else:
        form = GoalForm()
    return render(request, 'goals/add.html', {'form': form})

@login_required
def edit_goal(request, pk):
    try:
        goal = Goal.objects.get(pk=pk, user=request.user)
    except Goal.DoesNotExist:
        return redirect('goal_list')
    
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated successfully.')
            return redirect('goal_list')
    else:
        form = GoalForm(instance=goal)
    return render(request, 'goals/edit.html', {'form': form})

@login_required
def delete_goal(request, pk):
    try:
        goal = Goal.objects.get(pk=pk, user=request.user)
        if request.method == 'POST':
            goal.delete()
            messages.success(request, 'Goal deleted successfully.')
            return redirect('goal_list')
    except Goal.DoesNotExist:
        pass
    return redirect('goal_list')

@login_required
def spending_awareness(request):
    transactions = Transaction.objects.filter(user=request.user)
    expenses = transactions.filter(type='Expense')
    income = transactions.filter(type='Income')
    
    total_income = sum(t.amount for t in income)
    total_expenses = sum(t.amount for t in expenses)
    
    # Analyze categories
    category_totals = {}
    for t in expenses:
        category_totals[t.category] = category_totals.get(t.category, 0) + float(t.amount)
    
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    top_spending_category = sorted_categories[0] if sorted_categories else None
    
    tips = []
    alerts = []
    
    if total_income > 0:
        expense_ratio = (total_expenses / total_income) * 100
        if expense_ratio > 80:
            alerts.append(f"Warning: You have spent {expense_ratio:.1f}% of your income!")
        elif expense_ratio > 50:
            tips.append("You have spent over 50% of your income. Consider reviewing your budget.")
        else:
            tips.append("Great job! You are keeping your expenses low.")
    
    if top_spending_category:
        tips.append(f"Your highest spending is in '{top_spending_category[0]}'. Try to reduce it if possible.")
        
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'top_spending_category': top_spending_category,
        'tips': tips,
        'alerts': alerts,
    }
    return render(request, 'awareness.html', context)

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Notes'])
    
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    for t in transactions:
        writer.writerow([t.date, t.type, t.category, t.amount, t.notes])
        
    return response

@login_required
def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="financial_summary.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Financial Summary for {request.user.username}")
    
    transactions = Transaction.objects.filter(user=request.user)
    total_income = sum(t.amount for t in transactions if t.type == 'Income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'Expense')
    balance = total_income - total_expenses
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Total Income: ${total_income}")
    p.drawString(50, height - 100, f"Total Expenses: ${total_expenses}")
    p.drawString(50, height - 120, f"Balance: ${balance}")
    
    p.drawString(50, height - 150, "Recent Transactions:")
    y = height - 170
    for t in transactions.order_by('-date')[:20]:
        p.drawString(50, y, f"{t.date} - {t.type} - {t.category} - ${t.amount}")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50
            
    p.showPage()
    p.save()
    return response
