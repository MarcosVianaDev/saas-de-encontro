from django.urls import path
from . import views

urlpatterns = [
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
