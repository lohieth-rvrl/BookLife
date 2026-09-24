from django.urls import path, include
from .views import AddLibraianView,AddMemberView, home
from books.views import BookView, HoldListView, BorrowListView, GridBookView

app_name = 'base'

urlpatterns = [
    path('', home.as_view(), name='base_home'),
    path("add/libraian/", AddLibraianView.as_view(), name='add_lib'),
    path("add/member/", AddMemberView.as_view(), name='add_mem'),
    path("books/", BookView.as_view(), name="base_books"),
    path("books/gridview/", GridBookView.as_view(), name="base_gridbooks"),
    
    path("holds/", HoldListView.as_view(), name="base_holds"),
    path("borrows/", BorrowListView.as_view(), name="base_borrows"),
    
]
