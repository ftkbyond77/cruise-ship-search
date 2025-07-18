from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import SupervisorLoginView

urlpatterns = [
    path('', SupervisorLoginView.as_view(), name='login'),
    path('home/', views.home, name='home'),  
    path('person/<str:crew_id>/', views.person_detail, name='person_detail'),
    path('image/<str:image_id>/update/', views.update_image, name='update_image'),
    path('image/<str:image_id>/delete/', views.delete_image, name='delete_image'),
    path('debug-mongo/', views.test_mongo, name='mongo_debug'),
]