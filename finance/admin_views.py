from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Transaction, Goal
from django.db.models import Sum
from django.http import HttpResponse
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username == 'admin1' and password == 'password123':
            request.session['admin_user'] = username
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')
    
    return render(request, 'admin/login.html')

def admin_dashboard(request):
    if 'admin_user' not in request.session:
        return redirect('admin_login')
        
    total_users = User.objects.count()
    total_transactions = Transaction.objects.count()
    total_income = Transaction.objects.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Transaction.objects.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'total_users': total_users,
        'total_transactions': total_transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
    }
    return render(request, 'admin/dashboard.html', context)

def admin_logout(request):
    if 'admin_user' in request.session:
        del request.session['admin_user']
    return redirect('admin_login')

def admin_users(request):
    if 'admin_user' not in request.session:
        return redirect('admin_login')
    users = User.objects.all()
    return render(request, 'admin/users.html', {'users': users})

def delete_user(request, user_id):
    if 'admin_user' not in request.session:
        return redirect('admin_login')
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=user_id)
            user.delete()
            messages.success(request, 'User deleted successfully.')
        except User.DoesNotExist:
            pass
    return redirect('admin_users')

def admin_transactions(request):
    if 'admin_user' not in request.session:
        return redirect('admin_login')
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'admin/transactions.html', {'transactions': transactions})

def admin_export_csv(request):
    if 'admin_user' not in request.session:
        return redirect('admin_login')
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="system_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Date', 'Type', 'Category', 'Amount', 'Notes'])
    
    transactions = Transaction.objects.all().order_by('-date')
    for t in transactions:
        writer.writerow([t.user.username, t.date, t.type, t.category, t.amount, t.notes])
        
    return response

def admin_export_pdf(request):
    if 'admin_user' not in request.session:
        return redirect('admin_login')
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="system_report.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "SpendWise System Report")
    
    total_users = User.objects.count()
    total_transactions = Transaction.objects.count()
    total_income = Transaction.objects.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Transaction.objects.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Total Users: {total_users}")
    p.drawString(50, height - 100, f"Total Transactions: {total_transactions}")
    p.drawString(50, height - 120, f"Total Income: ${total_income}")
    p.drawString(50, height - 140, f"Total Expenses: ${total_expenses}")
    
    p.showPage()
    p.save()
    return response
