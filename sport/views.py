from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from datetime import date
from .models import Trainer, Slot, Booking, Review

def home(request):
    trainers = Trainer.objects.all()
    return render(request, 'home.html', {'trainers': trainers})

def trainer_detail(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    slots = trainer.slots.filter(date__gte=date.today())
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    show_only_free = request.GET.get('show_only_free')
    
    if date_from:
        slots = slots.filter(date__gte=date_from)
    if date_to:
        slots = slots.filter(date__lte=date_to)
    if show_only_free == 'on':
        slots = slots.filter(is_booked=False)
        
    slots = slots.order_by('date', "start_time")
    
    reviews = trainer.reviews.select_related('user').all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    user_review = None
    if request.user.is_authenticated:
        user_review = trainer.reviews.filter(user=request.user).first()
        
    return render(request, 'trainer_detail.html',
                  {
                    'trainer': trainer,
                    'slots': slots,
                    'date_from': date_from,
                    'date_to': date_to,
                    'show_only_free': show_only_free,
                    'reviews': reviews,
                    'avg_rating': avg_rating,
                    'user_review': user_review,   
                      })
                  
                  

@login_required
def book_slot(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id)

    # 1. Слот занят?
    if slot.is_booked:
        messages.error(request, 'Этот слот уже занят. Выберите другое время.')
        return redirect('sport:trainer_detail', trainer_id=slot.trainer.id)

    # 2. У пользователя уже есть активная бронь?
    if Booking.objects.filter(user=request.user).exists():
        messages.warning(
            request,
            'У вас уже есть активная запись. Чтобы записаться на другое время, '
            'сначала отмените текущую запись в личном кабинете.'
        )
        return redirect('users:profile')

    # 3. Создаём бронь
    Booking.objects.create(user=request.user, slot=slot)
    messages.success(request, f'Вы записаны на {slot.start_time}')
    return redirect('users:profile')


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    slot = booking.slot
    trainer_id = slot.trainer_id
    
    booking.delete()
    
    messages.success(request, "Запись успешно отменена")
    return redirect('users:profile')


# add_review — создание отзыва
@login_required  # Только авторизованные могут оставить отзыв
def add_review(request, trainer_id):  # request — запрос; trainer_id — id тренера из URL
    trainer = get_object_or_404(Trainer, id=trainer_id)  # Ищем тренера или 404

    # Если запрос НЕ POST (открыли URL в браузере) — не создаём отзыв, редирект
    if request.method != 'POST':
        return redirect('sport:trainer_detail', trainer_id=trainer.id)

    # Проверяем, не оставлял ли пользователь уже отзыв на этого тренера.
    # unique_together в модели запрещает дубли, но мы хотим показать красивое сообщение,
    # а не ошибку БД.
    if Review.objects.filter(trainer=trainer, user=request.user).exists():
        messages.error(request, 'Вы уже оставили отзыв на этого тренера.')
        return redirect('sport:trainer_detail', trainer_id=trainer.id)

    # Достаём оценку и текст из формы
    rating = request.POST.get('rating')  # строка '1'-'5' или None
    text = request.POST.get('text', '').strip()  # текст, пробелы по краям убраны

    # Валидация: оценка от 1 до 5, текст не пустой
    if rating not in ['1', '2', '3', '4', '5'] or not text:
        messages.error(request, 'Выберите оценку и напишите текст.')
        return redirect('sport:trainer_detail', trainer_id=trainer.id)

    # Создаём отзыв в базе данных
    Review.objects.create(
        trainer=trainer,        # к кому отзыв
        user=request.user,      # кто оставил
        rating=int(rating),     # оценка (int, не строка)
        text=text               # текст
    )
    messages.success(request, 'Спасибо за отзыв!')
    # Post-Redirect-Get: после POST редирект, чтобы F5 не отправил форму повторно
    return redirect('sport:trainer_detail', trainer_id=trainer.id)
    

# edit_review — редактирование
@login_required
def edit_review(request, review_id):
    # Ищем отзыв + проверяем, что он принадлежит текущему пользователю.
    # Чужой или несуществующий → 404. Это защита от подмены id в URL.
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
     # Если не POST — не редактируем, редирект на страницу тренера
    if request.method != "POST":
        return redirect('sport:trainer_detail', trainer_id=review.trainer.id)
    
    rating = request.POST.get('rating')
    text = request.POST.get('text', '').strip()
    
    # Валидация на сервере (HTML-required можно обойти)
    if rating not in ['1', '2', '3', '4', '5',] or not text:
        messages.error(request, "Выберите оценку и напишите текст.")
        return redirect('sport:trainer_detail', trainer_id = review.trainer.id)
    
    # Обновляем поля существующего объекта (не создаём новый!)
    review.rating = int(rating)
    review.text = text
    review.save()# Сохраняем в БД. Без этого изменения только в памяти.
    messages.success(request, "Отзыв обновлён.")
    return redirect('sport:trainer_detail', trainer_id = review.trainer.id)


# delete_review — удаление
@login_required
def delete_review(request, review_id):
    # 1. Ищем отзыв + проверяем владельца
    review = get_object_or_404(Review, id=review_id, user=request.user)

    # 2. Только POST (форма), не GET (ссылка)
    if request.method != 'POST':
        return redirect('sport:trainer_detail', trainer_id=review.trainer.id)

    # 3. ВАЖНО: сохраняем id тренера ДО удаления отзыва
    trainer_id = review.trainer.id   # ← вот эта строка должна быть!

    # 4. Удаляем отзыв
    review.delete()

    # 5. Сообщение и редирект (используем сохранённый trainer_id)
    messages.success(request, 'Отзыв удалён.')
    return redirect('sport:trainer_detail', trainer_id=trainer_id)