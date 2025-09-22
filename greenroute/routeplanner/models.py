from django.db import models
from django.contrib.auth.models import User

class RouteHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="routeplanner_routes"  # prevents reverse accessor clashes
    )
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    green_cover = models.FloatField()  # %
    pollution_index = models.FloatField()  # pollution API
    distance = models.FloatField(null=True, blank=True)  # km
    eco_cost = models.FloatField(null=True, blank=True)  # eco metric
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} ➝ {self.destination}"
