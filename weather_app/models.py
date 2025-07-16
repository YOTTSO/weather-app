from django.db import models

class WeatherQuery(models.Model):
    city_name = models.CharField(max_length=100)
    temperature = models.FloatField()
    description = models.CharField(max_length=255)
    query_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city_name} at {self.query_timestamp}"

    class Meta:
        ordering = ['-query_timestamp'] # noqa