from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from cruise_app.models import Person, CrewImage
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from datetime import datetime
from .mongo.mongo import db
import pprint

logger = logging.getLogger(__name__)

# Debug testing section
def test_mongo(request):
    persons = list(db.persons.find())
    out = f"Total persons: {len(persons)}\n\n"
    out += "\n".join([pprint.pformat(p) for p in persons])
    return HttpResponse(f"<pre>{out}</pre>")


from django.contrib.auth.views import LoginView

class SupervisorLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            messages.error(self.request, "Access denied. Only supervisors can log in.")
            return redirect('login')
        return super().form_valid(form)

@login_required
def home(request):
    raw_persons = list(db.persons.find())

    persons = []
    for p in raw_persons:
        crew_id = p.get("crew_id_number") or p.get("id_number")
        if crew_id:  
            p["crew_id"] = crew_id
            p["full_name"] = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            persons.append(p)

    return render(request, 'home.html', {'persons': persons})

@login_required
def person_detail(request, crew_id):
    try:
        person = db.persons.find_one({
            "$or": [
                {"crew_id_number": crew_id},
                {"id_number": crew_id}
            ]
        })

        if not person:
            logger.warning(f"No person found for crew_id or id_number: {crew_id}")
            return render(request, '404.html', status=404)

        person_obj = Person.objects.filter(
            crew_id_number=crew_id
        ).first() or Person.objects.filter(
            id_number=crew_id
        ).first()

        id_card_images = [
        img for img in person.get("images", [])
        if img.get("type") == "ID_CARD_FRONT"
    ]

        return render(request, 'detail.html', {
            'person': person,
            'id_card_images': id_card_images
        })

    except Exception as e:
        logger.error(f"Error retrieving person details for {crew_id}: {e}")
        return render(request, 'detail.html', status=404)

@login_required
def update_image(request, image_name):
    if not request.user.is_staff:
        raise PermissionDenied
    image = get_object_or_404(CrewImage, image__icontains=image_name)
    if request.method == 'POST':
        if 'image' in request.FILES:
            image.image = request.FILES['image']
            image.uploaded_at = datetime.now()
            image.save()
            messages.success(request, 'Image updated successfully.')
        else:
            messages.error(request, 'No image file provided.')
        return redirect('person_detail', crew_id=image.person.crew_id_number)
    return redirect('person_detail', crew_id=image.person.crew_id_number)

@login_required
def delete_image(request, image_name):
    if not request.user.is_staff:
        raise PermissionDenied
    image = get_object_or_404(CrewImage, image__icontains=image_name)
    crew_id = image.person.crew_id_number
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully.')
    return redirect('person_detail', crew_id=crew_id)
