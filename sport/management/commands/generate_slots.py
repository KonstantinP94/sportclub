from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
from sport.models import Trainer, Slot

class Command(BaseCommand):
    help = 'Генерирует слоты на неделю вперёд для всех тренеров'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        created_count = 0

        # Рабочие часы: с 9:00 до 18:00
        working_hours = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(13, 0), time(14, 0)),
            (time(14, 0), time(15, 0)),
            (time(15, 0), time(16, 0)),
            (time(16, 0), time(17, 0)),
            (time(17, 0), time(18, 0)),
        ]

        for trainer in Trainer.objects.all():
            for day_offset in range(7):  # на 7 дней вперёд
                current_date = today + timedelta(days=day_offset)
                for start, end in working_hours:
                    # get_or_create — не создаст дубликат, если слот уже есть
                    slot, created = Slot.objects.get_or_create(
                        trainer=trainer,
                        date=current_date,
                        start_time=start,
                        defaults={'end_time': end, 'is_booked': False}
                    )
                    if created:
                        created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Создано слотов: {created_count}'))