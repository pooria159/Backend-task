from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Book, BorrowRecord
from .serializers import BookSerializer, BorrowRecordSerializer, UserSerializer
from .permissions import IsAdmin, IsLibrarian, IsMember, role_required , IsLibrarianOrAdmin


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    def get_permissions(self):
        if self.action == 'borrow':
            permission_classes = [IsMember]
        elif self.action == 'return_book':
            permission_classes = [IsLibrarianOrAdmin]
        elif self.action in ['create', 'update', 'destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[IsMember])
    def borrow(self, request, pk=None):
        try:
            book = self.get_object()
        except Book.DoesNotExist:
            return Response({"error": "کتاب یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        if book.status != 'available':
            return Response({"error": "این کتاب در حال حاضر موجود نیست"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_borrows = BorrowRecord.objects.filter(
            user=request.user, 
            returned=False
        ).count()
        
        if active_borrows >= 3:
            return Response({"error": "شما حداکثر تعداد مجاز کتاب امانت گرفته‌اید"}, status=status.HTTP_400_BAD_REQUEST)
        
        borrow_record = BorrowRecord.objects.create(
            book=book,
            user=request.user,
            due_date=timezone.now() + timedelta(days=14)
        )
        
        book.status = 'borrowed'
        book.save()
        
        serializer = BorrowRecordSerializer(borrow_record)
        return Response({
            **serializer.data,
            "message": "کتاب با موفقیت امانت گرفته شد"
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsLibrarianOrAdmin])
    def return_book(self, request, pk=None):
        try:
            book = self.get_object()
        except Book.DoesNotExist:
            return Response({"error": "کتاب یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            borrow_record = BorrowRecord.objects.get(
                book=book, 
                returned=False
            )
        except BorrowRecord.DoesNotExist:
            return Response({"error": "سابقه امانت فعالی برای این کتاب یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        borrow_record.returned = True
        borrow_record.return_date = timezone.now()
        borrow_record.save()
        
        book.status = 'available'
        book.save()
        
        serializer = BorrowRecordSerializer(borrow_record)
        return Response({
            **serializer.data,
            "message": "کتاب با موفقیت بازگردانده شد"
        })

class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def borrowed_books(self, request):
        borrowed_books = BorrowRecord.objects.filter(
            user=request.user, 
            returned=False
        ).select_related('book')
        
        serializer = BorrowRecordSerializer(borrowed_books, many=True)
        return Response(serializer.data)