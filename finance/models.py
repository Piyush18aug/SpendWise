from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} - {self.category} - {self.amount}"

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.current_amount >= self.target_amount:
            self.is_completed = True
        else:
            self.is_completed = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min(int((self.current_amount / self.target_amount) * 100), 100)
        return 0

    @property
    def progress_bar_style(self):
        return f"width: {self.progress_percentage}%;"
