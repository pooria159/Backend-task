from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Book, BorrowRecord

class BookAPITestCase(APITestCase):
    def setUp(self):
        """
        ایجاد داده‌های اولیه برای تست
        """
        self.member_group, _ = Group.objects.get_or_create(name='Member')
        self.librarian_group, _ = Group.objects.get_or_create(name='Librarian') 
        self.admin_group, _ = Group.objects.get_or_create(name='Admin')
        
        self.member_user = User.objects.create_user(
            username='member', 
            password='password123'
        )
        self.member_user.groups.add(self.member_group)
        
        self.librarian_user = User.objects.create_user(
            username='librarian',
            password='password123'  
        )
        self.librarian_user.groups.add(self.librarian_group)
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.book1 = Book.objects.create(
            title='شازده کوچولو',
            author='آنتوان دو سنت اگزوپری',
            isbn='1234567890123',
            description='داستان زیبای شازده کوچولو',
            status='available'
        )
        
        self.book2 = Book.objects.create(
            title='صد سال تنهایی',
            author='گابریل گارسیا مارکز', 
            isbn='1234567890124',
            description='رمان معروف مارکز',
            status='available'
        )

    def test_list_books(self):
        """
        تست دریافت لیست کتاب‌ها
        """
        self.client.force_authenticate(user=self.member_user)
        
        response = self.client.get('/api/books/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_borrow_book_success(self):
        """
        تست امانت گرفتن کتاب با موفقیت
        """
        self.client.force_authenticate(user=self.member_user)
        
        response = self.client.post(f'/api/books/{self.book1.id}/borrow/')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'کتاب با موفقیت امانت گرفته شد')
        
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.status, 'borrowed')

    def test_borrow_book_max_limit(self):
        """
        تست محدودیت امانت گرفتن بیش از ۳ کتاب
        """
        self.client.force_authenticate(user=self.member_user)
        
        books = []
        for i in range(3):
            book = Book.objects.create(
                title=f'کتاب تست {i+1}',
                author='نویسنده تست',
                isbn=f'123456789012{i+10}',
                status='available'
            )
            books.append(book)
            self.client.post(f'/api/books/{book.id}/borrow/')
        
        response = self.client.post(f'/api/books/{self.book2.id}/borrow/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('حداکثر تعداد مجاز', response.data['error'])

    def test_return_book(self):
        """
        تست بازگرداندن کتاب
        """
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')
        
        self.client.force_authenticate(user=self.librarian_user)
        response = self.client.post(f'/api/books/{self.book1.id}/return_book/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'کتاب با موفقیت بازگردانده شد')
        
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.status, 'available')

    def test_permission_checks(self):
        """
        تست بررسی دسترسی‌های مختلف
        """
        self.client.force_authenticate(user=self.member_user)
        response = self.client.post('/api/books/', {
            'title': 'کتاب جدید',
            'author': 'نویسنده جدید', 
            'isbn': '1234567890129'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/books/', {
            'title': 'کتاب ایجاد شده توسط ادمین',
            'author': 'نویسنده ادمین',
            'isbn': '1234567890130'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        
    def test_borrow_unavailable_book(self):
        """
        تست امانت گرفتن کتابی که در دسترس نیست
        """
        self.client.force_authenticate(user=self.member_user)
        self.book1.status = 'borrowed'
        self.book1.save()

        response = self.client.post(f'/api/books/{self.book1.id}/borrow/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('در حال حاضر موجود نیست', response.data['error'])

    def test_borrow_book_without_authentication(self):
        """
        تست امانت گرفتن کتاب بدون احراز هویت
        """
        response = self.client.post(f'/api/books/{self.book1.id}/borrow/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_return_book_not_borrowed(self):
        """
        تست بازگرداندن کتابی که امانت داده نشده است
        """
        self.client.force_authenticate(user=self.librarian_user)
        response = self.client.post(f'/api/books/{self.book1.id}/return_book/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('سابقه امانت فعالی', response.data['error'])

    def test_non_librarian_cannot_return_book(self):
        """
        تست اینکه کاربر Member نمی‌تواند کتاب را بازگرداند
        """
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')

        response = self.client.post(f'/api/books/{self.book1.id}/return_book/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_borrowed_books_for_user(self):
        """
        تست API borrowed_books برای کاربر جاری
        """
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')

        response = self.client.get('/api/users/borrowed_books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['book'], self.book1.id)

    def test_admin_can_delete_book(self):
        """
        تست حذف کتاب توسط ادمین
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/books/{self.book1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=self.book1.id).exists())

    def test_librarian_cannot_add_book(self):
        """
        تست اینکه کتابدار اجازه افزودن کتاب ندارد
        """
        self.client.force_authenticate(user=self.librarian_user)
        response = self.client.post('/api/books/', {
            'title': 'کتاب جدید کتابدار',
            'author': 'نویسنده',
            'isbn': '1111111111111'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
