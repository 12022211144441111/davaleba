from django.db import models

class Person(models.Model):
    name = models.CharField()
    last_name = models.CharField()
    address = models.CharField()
    age = models.IntegerField()
    phone_number = models.CharField()

    def __str__(self):
        return f"{self.name}, {self.last_name}"

class Car(models.Model):
    model = models.CharField()
    brand = models.CharField()
    year = models.IntegerField()
    color = models.IntegerField()

    def __str__(self):
        return f"{self.brand} {self.model}"