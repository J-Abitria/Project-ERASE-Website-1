from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField(blank=True)
    hasRSVP = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.title}: {self.date} at {self.time}"

class RSVP(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    reserved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')
    
    def __str__(self):
        return f"{self.user.username} is RSVPed for {self.event.title}"