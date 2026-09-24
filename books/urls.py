from django.urls import path
from .views import BookView, BookListView, BookCreateView, BookUpdateView, BookDeleteView, BookDetailView, HoldBookView, HoldBookListView, HoldListView, DeleteHoldBook, HoldToBorrowView, ReturnHoldBook, BorrowBookView, BorrowBookListView, DeleteBorrowBook, ReturnBorrowBook

app_name = 'book'

urlpatterns = [
    # path('', BookView.as_view(), name='books'),
    path('list/', BookListView.as_view(), name='list'),
    path('create/', BookCreateView.as_view(), name='create_book'),
    path("update/<int:pk>/", BookUpdateView.as_view(), name="update_book"),
    path('delete/<int:pk>/', BookDeleteView.as_view(), name='delete_book'),
    path('detail/<int:pk>/', BookDetailView.as_view(), name='view_book'),

    path("<int:pk>/hold/", HoldBookView.as_view(), name="hold_book"),
    # path("", HoldListView.as_view(), name="holds"),
    path("holds/", HoldBookListView.as_view(), name="hold_list"),
    path("holds/<int:pk>/delete/", DeleteHoldBook.as_view(), name="hold_delete"),
    path("holds/<int:pk>/return/", ReturnHoldBook.as_view(), name="hold_return"),
    path("holds/borrow/<int:pk>/", HoldToBorrowView.as_view(), name="hold_to_borrow"),


    path("<int:pk>/borrow/", BorrowBookView.as_view(), name="borrow_book"),
    path("borrows/", BorrowBookListView.as_view(), name="borrow_list"),
    path("borrows/<int:pk>/delete/", DeleteBorrowBook.as_view(), name="borrow_delete"),
    path("borrows/<int:pk>/return/", ReturnBorrowBook.as_view(), name="borrow_return"),



    # path("borrow-direct/<int:pk>/", DirectBorrowView.as_view(), name="direct_borrow"),
    # path("return/<int:pk>/", ReturnBookView.as_view(), name="return_book"),
]
