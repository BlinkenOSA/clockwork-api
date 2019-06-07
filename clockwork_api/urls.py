from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    url(r'^authority/v1/', include('authority.urls', namespace='authority-v1')),
    url(r'^controlled_list/v1/', include('controlled_list.urls', namespace='controlled_list-v1')),
    path('admin/', admin.site.urls)

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
