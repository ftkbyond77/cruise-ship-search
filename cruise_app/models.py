from django.db import models

class CrewImage(models.Model):
    IMAGE_TYPES = [
        ('ID1', 'ID2'),
    ]

    crew_id_number = models.CharField(max_length=20)  
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES)
    image = models.ImageField(upload_to='uploads/')  
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crew_id_number} - {self.image_type}"
