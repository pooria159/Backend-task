from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Book, BorrowRecord


class JudgeBookTestCase(TestCase):

    def setUp(self):
        self.member_group, _ = Group.objects.get_or_create(name='Member')
        self.librarian_group, _ = Group.objects.get_or_create(name='Librarian')
        self.admin_group, _ = Group.objects.get_or_create(name='Admin')

        self.member_user = User.objects.create_user(username='member', password='password123')
        self.member_user.groups.add(self.member_group)

        self.librarian_user = User.objects.create_user(username='librarian', password='password123')
        self.librarian_user.groups.add(self.librarian_group)

        self.admin_user = User.objects.create_user(username='admin', password='password123')
        self.admin_user.groups.add(self.admin_group)

        self.book1 = Book.objects.create(
            title='شازده کوچولو',
            author='آنتوان دو سنت اگزوپری',
            isbn='1234567890123',
            description='داستان معروف',
            status='available'
        )

        self.book2 = Book.objects.create(
            title='صد سال تنهایی',
            author='گابریل گارسیا مارکز',
            isbn='1234567890124',
            description='رمان مشهور',
            status='available'
        )

        self.client = APIClient()

    def test_member_can_borrow_book(self):
        """کاربر Member می‌تواند کتاب موجود را امانت بگیرد"""
        self.client.force_authenticate(user=self.member_user)
        res = self.client.post(f'/api/books/{self.book1.id}/borrow/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.status, 'borrowed')

    def test_member_cannot_borrow_unavailable_book(self):
        """کاربر نمی‌تواند کتابی که قبلاً امانت گرفته شده را دوباره امانت بگیرد"""
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')
        res = self.client.post(f'/api/books/{self.book1.id}/borrow/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_borrow_book_limit(self):
        """کاربر بیش از ۳ کتاب نمی‌تواند امانت بگیرد"""
        self.client.force_authenticate(user=self.member_user)
        for i in range(3):
            book = Book.objects.create(
                title=f'کتاب {i+1}',
                author='تست',
                isbn=f'12345678901{i+20}',
                status='available'
            )
            self.client.post(f'/api/books/{book.id}/borrow/')

        res = self.client.post(f'/api/books/{self.book2.id}/borrow/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_librarian_cannot_return_book(self):
        """Member نمی‌تواند کتاب را بازگرداند"""
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')
        res = self.client.post(f'/api/books/{self.book1.id}/return_book/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_librarian_can_return_book(self):
        """Librarian می‌تواند کتاب را بازگرداند"""
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')

        self.client.force_authenticate(user=self.librarian_user)
        res = self.client.post(f'/api/books/{self.book1.id}/return_book/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.book1.refresh_from_db()
        self.assertEqual(self.book1.status, 'available')

    def test_member_cannot_add_book(self):
        """Member نمی‌تواند کتاب جدید اضافه کند"""
        self.client.force_authenticate(user=self.member_user)
        res = self.client.post('/api/books/', {
            'title': 'کتاب تست',
            'author': 'تست',
            'isbn': '1234567890999'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_add_book(self):
        """Admin می‌تواند کتاب جدید اضافه کند"""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post('/api/books/', {
            'title': 'کتاب ادمین',
            'author': 'ادمین',
            'isbn': '9999999999999'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_librarian_can_view_borrowed_books(self):
        """Librarian می‌تواند لیست کتاب‌های امانت داده‌شده را ببیند"""
        self.client.force_authenticate(user=self.member_user)
        self.client.post(f'/api/books/{self.book1.id}/borrow/')

        self.client.force_authenticate(user=self.librarian_user)
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
