from django.shortcuts import render, get_object_or_404
from django.db.models import Avg
from datetime import date
from .models import Trainer, Slot

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
                  