from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from accounts.views import AccountViewSet, login_view, logout_view
from appointments.views import AppointmentViewSet, PatientViewSet, SmsViewSet
from directory.views import DoctorViewSet, RoomViewSet, SpecializationViewSet
from schedule.views import PeriodViewSet, ShiftViewSet, SlotViewSet

router = DefaultRouter()
router.register('accounts', AccountViewSet, basename='account')
router.register('specializations', SpecializationViewSet)
router.register('doctors', DoctorViewSet)
router.register('rooms', RoomViewSet)
router.register('shifts', ShiftViewSet, basename='shift')
router.register('slots', SlotViewSet, basename='slot')
router.register('unavailability', PeriodViewSet, basename='period')
router.register('patients', PatientViewSet, basename='patient')
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('sms', SmsViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', login_view),
    path('api/auth/logout/', logout_view),
    path('api/', include(router.urls)),
    # одностраничное приложение Vue.js: все прочие адреса отдают index.html
    re_path(r'^(?!api/|admin/|assets/).*$', TemplateView.as_view(template_name='index.html')),
]
