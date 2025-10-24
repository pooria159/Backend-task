from rest_framework import serializers
from .models import Book, BorrowRecord
from django.contrib.auth.models import User

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'description', 'status', 'published_date', 'created_at']

class BorrowRecordSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = BorrowRecord
        fields = ['id', 'book', 'book_title', 'user', 'user_name', 'borrow_date', 'due_date', 'returned', 'return_date']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']