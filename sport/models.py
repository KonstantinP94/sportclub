from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import date

# Create your models here.

class Trainer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    specialization = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(validators=[MaxValueValidator(70)])
    photo = models.ImageField(upload_to='trainers', blank=True, null=True)
    description = models.TextField()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Slot(models.Model):
    trainer = models.ForeignKey('Trainer', on_delete=models.CASCADE, related_name="slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('trainer', 'date', 'start_time')
        
    def __str__(self):
        return f"Тренер: {self.trainer}, Дата: {self.date}, Время: {self.start_time}"
    
    
    def clean(self):
        if not self.pk and self.date and self.date < date.today():
            raise ValidationError({'date': 'Нельзя создавать слоты на прошедшую дату.'})
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'date':'Время окончания, должно быть позже времени начала'})
        
    
    @property
    def is_past(self):
        return self.date < date.today()
    
    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    slot = models.OneToOneField("Slot", on_delete=models.CASCADE, related_name='booking')
    created_at = models.DateTimeField(auto_now_add=True)
        
    def __str__(self):
        return f"{self.user} - {self.slot}"
    
        
class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
        
    trainer = models.ForeignKey('Trainer', on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now=True)
        
    class Meta:
        unique_together = ('trainer', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.trainer} - {self.rating}/5"
    

@receiver(post_save, sender=Booking)
def mark_slot_booked(sender, instance, created, **kwargs):
    if created:
        instance.slot.is_booked = True
        instance.slot.save()
        
@receiver(post_delete, sender=Booking)
def mark_slot_free(sender, instance, **kwargs):
    instance.slot.is_booked = False
    instance.slot.save()
        