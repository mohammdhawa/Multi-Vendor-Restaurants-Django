from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from marketplace.views import cart, search, checkout

urlpatterns = [
       path('admin/', admin.site.urls),
       path('', views.home, name='home'),
       path('', include('accounts.urls')),
       path('marketplace/', include('marketplace.urls')),

       path('cart/', cart, name='cart'),
       path('search/', search, name='search'),

       path('checkout/', checkout, name='checkout'),

       path('orders/', include('orders.urls')),

       path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
