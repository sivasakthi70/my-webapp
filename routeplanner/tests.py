from django.test import TestCase
from .models import Route

class RouteModelTest(TestCase):
    def test_route_creation(self):
        route = Route.objects.create(
            source='Madurai',
            destination='Tenkasi',
            green_cover=60.0,
            pollution_index=40.0,
            distance_km=160.0,
            eco_cost=260.0
        )
        self.assertEqual(route.source, 'Madurai')
        self.assertEqual(route.destination, 'Tenkasi')
