from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from datetime import date
from .models import Trainer, Slot, Booking

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
    
    if slot.is_booked:
        messages.error(request, 'Этот слот занят, выберите другое время.')
        return redirect('sport:trainer_detail', trainer_id=slot.trainer_id)
    
    Booking.objects.create(user=request.user, slot=slot)
    
    messages.success(request, f'Вы записаны на {slot.start_time}')
    return redirect('sport:trainer_detail', trainer_id=slot.trainer_id)


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    slot = booking.slot
    trainer_id = slot.trainer_id
    
    booking.delete()
    
    messages.succes(request, "Запись успешно отменена")
    return redirect('sport:trainer_detail', trainer_id=trainer_id)