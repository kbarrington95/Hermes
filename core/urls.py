from django.views.generic import TemplateView
from django.urls import path

# URLConf
urlpatterns = [
    path('', TemplateView.as_view(template_name='core/index.html')),
    path('login/', TemplateView.as_view(template_name='core/login.html')),
    path('register/', TemplateView.as_view(template_name='core/register.html')),
]