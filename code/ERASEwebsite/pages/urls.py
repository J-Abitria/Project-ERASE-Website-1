from django.urls import path
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

from . import views
from students.views import StudentDatabaseView
from workshops.views import ShipmentMapView
from reports.views import (
    ReportsDashboardView,
    ReportsPdfView,
    DeleteFundingView,
    DeleteWorkshopAttendanceView,
    DeleteStudentSupportView,
    DeleteSocialMediaView,
)
from event_calendar.views import (
    CalendarView,
    AddEventView,
    RSVPEventView,
    RSVPListingView,
    RSVPDetailView,
)

app_name = 'pages'

urlpatterns = [
    # Core & Authentication
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='pages:home'), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('account/', views.AccountView.as_view(), name='account'),
    path('account/delete/', views.DeleteAccountView.as_view(), name='delete_account'),
    path('manage-users/', views.ManageUsersView.as_view(), name='manage_users'),
    path('admin-panel/', views.CustomAdminView.as_view(), name='custom_admin'),

    # Event Calendar
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('calendar/add-event/', AddEventView.as_view(), name='add_event'),
    path('calendar/rsvp/<int:event_id>/', RSVPEventView.as_view(), name='rsvp_event'),
    path('rsvp-listing/', RSVPListingView.as_view(), name='rsvp_listing'),
    path('rsvp-listing/<int:event_id>/', RSVPDetailView.as_view(), name='rsvp_detail'),

    # Workshops & Shipment Map
    path('shipment-map/', ShipmentMapView.as_view(), name='shipment_map'),

    # Student Database
    path('studentdb/', StudentDatabaseView.as_view(), name='studentdb'),

    # Reports & Analytics
    path('reports/', ReportsDashboardView.as_view(), name='reports'),
    path('reports/export/pdf/', ReportsPdfView.as_view(), name='reports_pdf'),
    path('reports/delete-funding/<int:pk>/', DeleteFundingView.as_view(), name='delete_funding'),
    path('reports/delete-workshop/<int:pk>/', DeleteWorkshopAttendanceView.as_view(), name='delete_workshop'),
    path('reports/delete-student/<int:pk>/', DeleteStudentSupportView.as_view(), name='delete_student'),
    path('reports/delete-social/<int:pk>/', DeleteSocialMediaView.as_view(), name='delete_social'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)