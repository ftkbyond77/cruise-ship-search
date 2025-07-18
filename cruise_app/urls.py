from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('person/<str:crew_id>/', views.person_detail, name='person_detail'),
    path('image/<int:image_id>/update/', views.update_image, name='update_image'),
    path('image/<int:image_id>/delete/', views.delete_image, name='delete_image'),
    path('debug-mongo/', views.test_mongo, name='mongo_debug'),
]