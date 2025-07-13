from django.core.management.base import BaseCommand
from cruise_app.models import Person, CrewImage
from cruise_app.mongo.mongo import db
from django.core.files import File
import os
from django.conf import settings
from datetime import datetime

class Command(BaseCommand):
    help = 'Sync MongoDB persons and images to Django models'

    def handle(self, *args, **kwargs):
        # Sync Persons
        for person_data in db.persons.find():
            person, created = Person.objects.get_or_create(
                crew_id_number=person_data['crew_id_number'],
                defaults={
                    'first_name': person_data['first_name'],
                    'middle_name': person_data.get('middle_name', ''),
                    'last_name': person_data['last_name'],
                    'full_name': person_data['full_name'],
                    'birth_date': person_data['birth_date'],
                    'age': person_data['age'],
                    'gender': person_data['gender'],
                    'height_m': person_data['height_m'],
                    'weight_kg': person_data['weight_kg'],
                    'hair_color': person_data['hair_color'],
                    'eye_color': person_data['eye_color'],
                    'passport_number': person_data['passport_number'],
                    'nationality': person_data['nationality'],
                    'position': person_data['position'],
                    'crew_id_expire': person_data['crew_id_expire'],
                    'address_philippines': person_data['address_philippines'],
                    'address_usa': person_data['address_usa'],
                    'place_of_birth': person_data['place_of_birth'],
                    'arrival_mode': person_data['arrival_mode'],
                    'cbp_permit_expire': person_data['cbp_permit_expire'],
                    'ship': person_data['ship'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Person: {person.full_name}"))
            else:
                self.stdout.write(f"Updated Person: {person.full_name}")

            # Sync Images
            for img in person_data.get('images', []):
                if img['type'] == 'ID_CARD_FRONT':
                    file_path = os.path.join(settings.MEDIA_ROOT, img['path'])
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            django_file = File(f)
                            crew_image, img_created = CrewImage.objects.get_or_create(
                                person=person,
                                image_type=img['type'],
                                uploaded_at=img['uploaded_at'],
                                defaults={'image': django_file}
                            )
                            if img_created:
                                crew_image.image.save(os.path.basename(img['path']), django_file)
                                self.stdout.write(self.style.SUCCESS(f"Created Image for {person.crew_id_number}"))
                            else:
                                self.stdout.write(f"Image already exists for {person.crew_id_number}")

        # Update existing CrewImage records with no person
        for crew_image in CrewImage.objects.filter(person__isnull=True):
            try:
                # Adjust this logic based on your image naming convention
                crew_id = crew_image.image.name.split('/')[-1].split('_')[1]
                person = Person.objects.get(crew_id_number=crew_id)
                crew_image.person = person
                crew_image.save()
                self.stdout.write(self.style.SUCCESS(f"Updated CrewImage person for {person.crew_id_number}"))
            except (Person.DoesNotExist, IndexError):
                self.stdout.write(self.style.WARNING(f"No Person found for CrewImage with image {crew_image.image.name}"))