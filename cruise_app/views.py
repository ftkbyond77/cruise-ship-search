from django.shortcuts import render
from .mongo.mongo import db  

def person_list(request):
    persons = list(db.persons.find())
    return render(request, 'person_list.html', {'persons': persons})

def person_detail(request, crew_id):
    person = db.persons.find_one({"crew_id_number": crew_id})
    return render(request, 'person_detail.html', {'person': person})