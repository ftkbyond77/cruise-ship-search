from django.shortcuts import render, get_object_or_404
from .mongo.mongo import db
from .models import CrewImage

def home(request):
    persons = list(db.persons.find())
    return render(request, 'home.html', {'persons': persons})

def person_detail(request, crew_id):
    person = db.persons.find_one({'crew_id_number': crew_id})
    images = CrewImage.objects.filter(crew_id_number=crew_id)
    return render(request, 'detail.html', {'person': person, 'images': images})

