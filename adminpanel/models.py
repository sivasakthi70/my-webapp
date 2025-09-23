# adminpanel/models.py
from django.db import models
from django.contrib.auth.models import User

class RouteHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance_km = models.FloatField()
    pollution_index = models.FloatField()
    green_cover = models.FloatField()   # store numeric value (e.g., 37.5)
    eco_cost = models.FloatField()
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.source} → {self.destination}"
