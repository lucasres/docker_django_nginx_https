from django.urls import path
from api.views import index

urlpatterns = [
    path('',index,name='api-home')
]
