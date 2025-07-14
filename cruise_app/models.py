from django.db import models
from django.core.exceptions import ValidationError
from .mongo.mongo import db

def validate_crew_id_number(value):
    if not db.persons.find_one({'crew_id_number': value}):
        raise ValidationError(f"No person found with crew_id_number: {value}")

class Person(models.Model):
    crew_id_number = models.CharField(max_length=20, unique=True, validators=[validate_crew_id_number])
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=150)
    birth_date = models.DateField()
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    height_m = models.FloatField()
    weight_kg = models.FloatField()
    hair_color = models.CharField(max_length=50)
    eye_color = models.CharField(max_length=50)
    passport_number = models.CharField(max_length=20)
    nationality = models.CharField(max_length=2)
    position = models.CharField(max_length=50)
    crew_id_expire = models.CharField(max_length=10)
    address_philippines = models.CharField(max_length=200)
    address_usa = models.CharField(max_length=200)
    place_of_birth = models.CharField(max_length=100)
    arrival_mode = models.CharField(max_length=50)
    cbp_permit_expire = models.DateField()
    ship = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.full_name} ({self.crew_id_number})"

class CrewImage(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image_type = models.CharField(max_length=50, default='ID_CARD_FRONT')
    image = models.ImageField(upload_to='idcards/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person.crew_id_number if self.person else 'No Person'} - {self.image_type}"