from django.urls import path
from . import views
from .event_admin import JoinView, AdminBootstrapView, AdminParticipantActionView, AdminCaseActionView, AdminEvidenceContentView, AdminPhotoContentView
from .event_operations import EventTransitionView, EventConfigurationView
from .global_admin import GlobalView
from .event_requests import EventRequestView
from .contexts import ContextView, GlobalEventContextView
from .team import TeamView
from .profile_operations import ActivationView, OutfitView, OutfitContentView, ProfileInterventionView, ProfileFieldsView, ProfileDispositionView
from .social_safety import BlockView,ReportView
from .support import SupportView,AdminSupportView
from .passes import LikesReceivedView,AdminPassView,FinancialReportView
from .location import LocationView,LocationExceptionView,LocationHistoryView,LocationDecisionView
from .notifications import NotificationView,AnnouncementView

urlpatterns = [
    path('outfits/<uuid:participant_id>/content/',OutfitContentView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/profile-intervention/',ProfileInterventionView.as_view()),
    path('notifications/',NotificationView.as_view()),
    path('event-admin/announcements/',AnnouncementView.as_view()),
    path('location/',LocationView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/location-decision/',LocationDecisionView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/location-exception/',LocationExceptionView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/location-history/',LocationHistoryView.as_view()),
    path('likes-received/',LikesReceivedView.as_view()),
    path('event-admin/passes/',AdminPassView.as_view()),
    path('event-admin/financial/',FinancialReportView.as_view()),
    path('blocks/<uuid:peer_id>/',BlockView.as_view()),
    path('reports/',ReportView.as_view()),
    path('reports/<uuid:peer_id>/',ReportView.as_view()),
    path('support/',SupportView.as_view()),
    path('event-admin/support/',AdminSupportView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/activate/',ActivationView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/outfit/',OutfitView.as_view()),
    path('profile/fields/',ProfileFieldsView.as_view()),
    path('profile/disposition/',ProfileDispositionView.as_view()),
    path('contexts/',ContextView.as_view()),
    path('global/',GlobalView.as_view()),
    path('global/event/',GlobalEventContextView.as_view()),
    path('event-admin/team/',TeamView.as_view()),
    path('event-admin/requests/', EventRequestView.as_view()),
    path('event-admin/transition/', EventTransitionView.as_view()),
    path('event-admin/configuration/', EventConfigurationView.as_view()),
    path('join/<str:token>/', JoinView.as_view()),
    path('event-admin/', AdminBootstrapView.as_view()),
    path('event-admin/evidence/<uuid:evidence_id>/content/', AdminEvidenceContentView.as_view()),
    path('event-admin/photos/<uuid:photo_id>/content/', AdminPhotoContentView.as_view()),
    path('event-admin/participants/<uuid:participant_id>/action/', AdminParticipantActionView.as_view()),
    path('event-admin/cases/<uuid:case_id>/action/', AdminCaseActionView.as_view()),
    path("session/", views.SessionView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("bootstrap/", views.BootstrapView.as_view()),
    path("profile/", views.ProfileView.as_view()),
    path("profile/photos/", views.PhotosView.as_view()),
    path("filters/", views.FiltersView.as_view()),
    path("participants/", views.ParticipantsView.as_view()),
    path("participants/<uuid:peer_id>/", views.ParticipantView.as_view()),
    path("discovery/", views.DiscoveryView.as_view()),
    path("interactions/<uuid:peer_id>/", views.InteractionView.as_view()),
    path("favorites/<uuid:peer_id>/", views.FavoriteView.as_view()),
    path("conversations/", views.ConversationsView.as_view()),
    path("conversations/<uuid:peer_id>/messages/", views.MessagesView.as_view()),
    path("matches/<uuid:peer_id>/end/", views.EndMatchView.as_view()),
    path("photos/<uuid:photo_id>/content/", views.PhotoContentView.as_view()),
]
