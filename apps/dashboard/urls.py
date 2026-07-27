from django.urls import path

from .views import DashboardView

# Sem app_name/namespace de propósito: o dashboard vive na raiz do site e
# é referenciado como {% url 'home' %} em todo o projeto (menu lateral,
# LOGIN_REDIRECT_URL etc.).
urlpatterns = [
    path('', DashboardView.as_view(), name='home'),
]
