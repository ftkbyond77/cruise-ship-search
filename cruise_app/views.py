from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from cruise_app.models import Person, CrewImage
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import logging
from datetime import datetime
from .mongo.mongo import db
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

# debug testing section
from django.http import HttpResponse
import pprint

def test_mongo(request):
    persons = list(db.persons.find())
    out = f"Total persons: {len(persons)}\n\n"
    out += "\n".join([pprint.pformat(p) for p in persons])
    return HttpResponse(f"<pre>{out}</pre>")

def home(request):
    persons = list(db.persons.find())  
    return render(request, 'home.html', {'persons': persons})

# def person_detail(request, crew_id):
#     logger.debug(f"Fetching person with crew_id: {crew_id}")
#     person = get_object_or_404(Person, crew_id_number=crew_id)
#     id_card_images = person.images.filter(image_type='ID_CARD_FRONT')
#     logger.debug(f"Found {id_card_images.count()} ID_CARD_FRONT images for crew_id: {crew_id}")
#     return render(request, 'detail.html', {'person': person, 'id_card_images': id_card_images})

def person_detail(request, crew_id):
    person = db.persons.find_one({"crew_id_number": crew_id})

    if not person:
        return render(request, '404.html', status=404)

    # ดึงเฉพาะภาพที่ type = ID_CARD_FRONT
    id_card_images = [
        img for img in person.get("images", [])
        if img.get("type") == "ID_CARD_FRONT"
    ]

    return render(request, 'detail.html', {
        'person': person,
        'id_card_images': id_card_images
    })

@login_required
def update_image(request, image_id):
    if not request.user.is_staff:
        raise PermissionDenied
    image = get_object_or_404(CrewImage, id=image_id)
    if request.method == 'POST':
        if 'image' in request.FILES:
            image.image = request.FILES['image']
            image.uploaded_at = datetime.now()
            image.save()
            messages.success(request, 'Image updated successfully.')
            return redirect('person_detail', crew_id=image.person.crew_id_number)
        else:
            messages.error(request, 'No image file provided.')
    return render(request, 'update_image.html', {'image': image})

@login_required
def delete_image(request, image_id):
    if not request.user.is_staff:
        raise PermissionDenied
    image = get_object_or_404(CrewImage, id=image_id)
    if request.method == 'POST':
        crew_id = image.person.crew_id_number
        image.delete()
        messages.success(request, 'Image deleted successfully.')
        return redirect('person_detail', crew_id=crew_id)
    return render(request, 'delete_image.html', {'image': image})
