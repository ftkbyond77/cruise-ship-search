from django.core.management.base import BaseCommand
from cruise_app.models import Person, CrewImage
from cruise_app.mongo.mongo import db
from django.core.files import File
from django.conf import settings
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Sync MongoDB persons and images to Django models'

    def handle(self, *args, **kwargs):
        print(f"MONGO_DB_NAME = {db.name}")
        print(f"MONGO_URI = {os.environ.get('MONGO_URI')}")

        for person_data in db.persons.find():
            try:
                crew_id = person_data.get('crew_id_number')
                if not crew_id:
                    continue

                def get_safe_float(value):
                    try:
                        return float(value) if value not in [None, '', 'Null'] else None
                    except:
                        return None

                def get_safe_int(value):
                    try:
                        return int(value) if value not in [None, '', 'Null'] else None
                    except:
                        return None

                def get_safe_date(value):
                    try:
                        if isinstance(value, datetime):
                            return value
                        return datetime.strptime(value, "%Y-%m-%d") if value else None
                    except:
                        return None

                person_defaults = {
                    'first_name': person_data.get('first_name', ''),
                    'middle_name': person_data.get('middle_name', ''),
                    'last_name': person_data.get('last_name', ''),
                    'full_name': person_data.get('full_name', ''),
                    'birth_date': get_safe_date(person_data.get('birth_date')),
                    'age': get_safe_int(person_data.get('age')),
                    'gender': person_data.get('gender', ''),
                    'height_m': get_safe_float(person_data.get('height_m')),
                    'weight_kg': get_safe_float(person_data.get('weight_kg')),
                    'hair_color': person_data.get('hair_color', ''),
                    'eye_color': person_data.get('eye_color', ''),
                    'passport_number': person_data.get('passport_number', ''),
                    'nationality': person_data.get('nationality', ''),
                    'position': person_data.get('position', ''),
                    'crew_id_expire': get_safe_date(person_data.get('crew_id_expire')),
                    'address_philippines': person_data.get('address_philippines', ''),
                    'address_usa': person_data.get('address_usa', ''),
                    'place_of_birth': person_data.get('place_of_birth', ''),
                    'arrival_mode': person_data.get('arrival_mode', ''),
                    'cbp_permit_expire': get_safe_date(person_data.get('cbp_permit_expire')),
                    'ship': person_data.get('ship', ''),
                }

                person, created = Person.objects.get_or_create(
                    crew_id_number=crew_id,
                    defaults=person_defaults
                )

                if not created:
                    for key, val in person_defaults.items():
                        setattr(person, key, val)
                    person.save()
                    self.stdout.write(f"Updated Person: {person.full_name}")
                else:
                    self.stdout.write(self.style.SUCCESS(f"Created Person: {person.full_name}"))

                # Handle image
                for img in person_data.get('images', []):
                    if img.get('type') == 'ID_CARD_FRONT':
                        image_path = os.path.join(settings.MEDIA_ROOT, img.get('path', ''))

                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as f:
                                django_file = File(f)
                                crew_image, img_created = CrewImage.objects.get_or_create(
                                    person=person,
                                    image_type='ID_CARD_FRONT',
                                    uploaded_at=img.get('uploaded_at') or None,
                                    defaults={'image': django_file}
                                )
                                if img_created:
                                    crew_image.image.save(os.path.basename(image_path), django_file)
                                    self.stdout.write(self.style.SUCCESS(f"Created Image for {crew_id}"))
                        else:
                            self.stdout.write(f"Image file not found: {image_path}")

            except Exception as e:
                self.stderr.write(f"Error syncing person: {e}")
