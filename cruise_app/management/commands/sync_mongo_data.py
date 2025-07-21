from django.core.management.base import BaseCommand
from cruise_app.models import Person, CrewImage
from cruise_app.mongo.mongo import db
from django.core.files import File
from django.conf import settings
from datetime import datetime
import os
import logging

class Command(BaseCommand):
    help = 'Sync MongoDB persons and images to Django models'

    FIELD_MAPPINGS = {
        'first_name': {'type': 'str', 'default': ''},
        'middle_name': {'type': 'str', 'default': ''},
        'last_name': {'type': 'str', 'default': ''},
        'full_name': {'type': 'str', 'default': ''},
        'birth_date': {'type': 'date', 'default': None},
        'birth_data': {'type': 'date', 'default': None},  # typo fallback
        'age': {'type': 'int', 'default': None},
        'gender': {'type': 'str', 'default': ''},
        'height_m': {'type': 'float', 'default': None},
        'height_f': {'type': 'float', 'default': None},  # optional fallback
        'weight_kg': {'type': 'float', 'default': None},
        'weight_p': {'type': 'float', 'default': None},  # optional fallback
        'hair_color': {'type': 'str', 'default': ''},
        'eye_color': {'type': 'str', 'default': ''},
        'passport_number': {'type': 'str', 'default': ''},
        'nationality': {'type': 'str', 'default': ''},
        'position': {'type': 'str', 'default': ''},
        'crew_id_number': {'type': 'str', 'default': ''},
        'id_number': {'type': 'str', 'default': ''},
        'crew_id_expire': {'type': 'date', 'default': None},
        'address_philippines': {'type': 'str', 'default': ''},
        'address_usa': {'type': 'str', 'default': ''},
        'address_home': {'type': 'str', 'default': ''},
        'place_of_birth': {'type': 'str', 'default': ''},
        'arrival_mode': {'type': 'str', 'default': ''},
        'cbp_permit_expire': {'type': 'date', 'default': None},
        'chp_permit_expire': {'type': 'date', 'default': None},  # typo fallback
        'passport_exp': {'type': 'date', 'default': None},
        'permit_type': {'type': 'str', 'default': ''},
        'permit_country': {'type': 'str', 'default': ''},
        'permit_state': {'type': 'str', 'default': ''},
        'issue_date': {'type': 'date', 'default': None},
        'expired_date': {'type': 'date', 'default': None},
        'ship': {'type': 'str', 'default': ''},
        'external_id': {'type': 'str', 'default': ''},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def get_safe_value(self, value, field_type):
        try:
            if value in [None, '', 'Null']:
                return None
            if field_type == 'str':
                return str(value)
            elif field_type == 'int':
                return int(float(value))
            elif field_type == 'float':
                return float(value)
            elif field_type == 'date':
                if isinstance(value, datetime):
                    return value
                date_formats = ["%Y-%m-%d", "%Y-%m", "%Y-%m-%dT%H:%M:%S.%fZ"]
                for fmt in date_formats:
                    try:
                        return datetime.strptime(str(value), fmt)
                    except ValueError:
                        continue
                return None
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to convert value {value} to {field_type}: {e}")
            return None
        return None

    def handle(self, *args, **kwargs):
        self.stdout.write(f"MONGO_DB_NAME = {db.name}")
        self.stdout.write(f"MONGO_URI = {os.environ.get('MONGO_URI')}")

        # Get list of actual model field names for Person to filter valid fields only
        model_fields = [
            f.name for f in Person._meta.get_fields()
            if f.concrete and not f.many_to_many and not f.auto_created
        ]

        for person_data in db.persons.find():
            try:
                crew_id = person_data.get('crew_id_number') or person_data.get('id_number')
                if not crew_id:
                    self.logger.warning("Skipping record: Missing both crew_id_number and id_number")
                    continue

                # Build dict with safe type conversions for available fields only
                person_defaults = {}
                for field, config in self.FIELD_MAPPINGS.items():
                    if field in person_data:
                        val = self.get_safe_value(person_data[field], config['type'])
                        if val is None:
                            val = config['default']
                        person_defaults[field] = val

                # Height/weight unit conversion if applicable
                if person_defaults.get('height_f'):
                    person_defaults['height_m'] = person_defaults['height_f'] * 0.3048
                if person_defaults.get('weight_p'):
                    person_defaults['weight_kg'] = person_defaults['weight_p'] * 0.453592

                # Filter out fields not in Django model to avoid errors
                filtered_defaults = {
                    k: v for k, v in person_defaults.items() if k in model_fields
                }

                # Create or update Person
                person, created = Person.objects.get_or_create(
                    crew_id_number=crew_id,
                    defaults=filtered_defaults
                )
                if not created:
                    for key, val in filtered_defaults.items():
                        setattr(person, key, val)
                    person.save()
                    self.stdout.write(f"Updated Person: {person.full_name}")
                else:
                    self.stdout.write(self.style.SUCCESS(f"Created Person: {person.full_name}"))

                # Process images
                supported_image_types = ['ID_CARD_FRONT', 'CBP_PERMIT', 'DRIVER_LICENSE']
                for img in person_data.get('images', []):
                    image_type = img.get('type')
                    if image_type not in supported_image_types:
                        self.logger.warning(f"Unsupported image type: {image_type}")
                        continue

                    image_path = os.path.join(settings.MEDIA_ROOT, img.get('path', ''))
                    if not os.path.exists(image_path):
                        self.logger.warning(f"Image file not found: {image_path}")
                        continue

                    # Check if image already exists
                    exists = CrewImage.objects.filter(
                        person=person, image_type=image_type
                    ).exists()
                    if exists:
                        self.stdout.write(f"Image already exists for {crew_id}: {image_type}")
                        continue

                    # Create new CrewImage
                    with open(image_path, 'rb') as f:
                        django_file = File(f)
                        crew_image = CrewImage.objects.create(
                            person=person,
                            image_type=image_type,
                            uploaded_at=self.get_safe_value(img.get('uploaded_at'), 'date')
                        )
                        crew_image.image.save(os.path.basename(image_path), django_file)
                        self.stdout.write(self.style.SUCCESS(f"Created {image_type} Image for {crew_id}"))

            except Exception as e:
                self.logger.error(f"Error syncing person {crew_id}: {e}")
                self.stderr.write(f"Error syncing person {crew_id}: {e}")
