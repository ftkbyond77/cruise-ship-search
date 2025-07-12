from django.urls import path
from . import views

urlpatterns = [
    path('persons/', views.person_list, name='person_list'),
    path('person/<str:crew_id>/', views.person_detail, name='person_detail'),

]