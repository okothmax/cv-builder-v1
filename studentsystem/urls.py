from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('studentpage.urls')),
    path('studentpage/', include('studentpage.urls')),
    path('teacherpage/', include('teacherpage.urls')),
    path('attendancepage/', include('attendancepage.urls')),
    path('account/', include('account.urls')),
    path('audio/', include('audio.urls')),
    path('video/', include('video.urls')),
    path('exambank/', include('exambank.urls')),
    path('files/', include('files.urls')),
    path('payments/', include('payments.urls')),
    path('academics/', include('academics.urls')),
    path('invoices/', include('invoices.urls')),
    path('reports/', include('reports.urls')),
    path('schooldocuments/', include('schooldocuments.urls')),
    path('qrcodes/', include('qrcodes.urls')),
    path('adminresume/', include('adminresume.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
