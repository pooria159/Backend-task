from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Book(models.Model):
    STATUS_CHOICES = [
        ('available', 'موجود'),
        ('borrowed', 'امانت داده شده'),
        ('maintenance', 'در تعمیر و نگهداری'),
    ]
    
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    published_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class BorrowRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned = models.BooleanField(default=False)
    return_date = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now() + timedelta(days=14)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
    
    def has_permission(self, action, user):
        is_member = user.groups.filter(name='Member').exists()
        is_librarian = user.groups.filter(name='Librarian').exists()
        is_admin = user.groups.filter(name='Admin').exists() or user.is_superuser
        
        permissions_map = {
            'borrow_book': is_member or is_librarian or is_admin,
            'return_book': is_librarian or is_admin,
            'add_book': is_admin,
            'delete_book': is_admin,
            'view_borrow_history': is_librarian or is_admin,
        }
        
        return permissions_map.get(action, False)