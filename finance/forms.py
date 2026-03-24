from django import forms
from django.contrib.auth.models import User
from .models import Transaction, Goal

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'category', 'amount', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'target_amount', 'current_amount']
