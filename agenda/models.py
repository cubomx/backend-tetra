from django.db import models

# Create your models here.
class Event(models.Model):
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField("Fecha de evento")