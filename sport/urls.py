from django.urls import path
from . import views

app_name = 'sport'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('trainer/<int:trainer_id>/', views.trainer_detail, name="trainer_detail"),
    path('book_slot/<int:slot_id>/', views.book_slot, name="book_slot"),
    path('cancel_booking/<int:booking_id>/', views.cancel_booking, name="cancel_booking"),
    # Создание отзыва: POST на /sport/add_review/<trainer_id>/
    path('add_review/<int:trainer_id>/', views.add_review, name='add_review'),
    # Редактирование: POST на /sport/edit_review/<review_id>/
    path('edit_review/<int:review_id>/', views.edit_review, name='edit_review'),
    # Удаление: POST на /sport/delete_review/<review_id>/
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),
    
]