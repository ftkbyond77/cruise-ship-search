from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from cruise_app.models import Person, CrewImage
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def home(request):
    persons = Person.objects.all()
    return render(request, 'home.html', {'persons': persons})

def person_detail(request, crew_id):
    logger.debug(f"Fetching person with crew_id: {crew_id}")
    person = get_object_or_404(Person, crew_id_number=crew_id)
    id_card_images = person.images.filter(image_type='ID_CARD_FRONT')
    logger.debug(f"Found {id_card_images.count()} ID_CARD_FRONT images for crew_id: {crew_id}")
    return render(request, 'detail.html', {'person': person, 'id_card_images': id_card_images})

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