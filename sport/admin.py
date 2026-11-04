from django.contrib import admin
from .models import Trainer, Slot, Booking, Review

admin.site.register(Trainer)
admin.site.register(Booking)
admin.site.register(Review)

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("trainer", "date", "start_time", "end_time", "is_booked")
    list_filter = ("trainer", "is_booked", "date")
    search_field = ("trainer__first_name", "trainer__last_name")
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return("date",)
        return ()