from django.urls import path
from . import views  # Assuming you have views defined in aiLoad/views.py

urlpatterns = [
    path('', views.index, name='index'),  # Example route
    path('compareCompatability/',views.predict_compatibility,name='predict_compatibility'),
    path('sendMail/',views.send_email,name='send_email'),
  
  

]
