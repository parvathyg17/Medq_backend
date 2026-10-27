from django.urls import path
from .views import ContactMessageSubmitView, ContactMessageListView, ChatAssistantView

urlpatterns = [
    path('submit', ContactMessageSubmitView.as_view(), name='contact_submit_legacy'),
    path('submit/', ContactMessageSubmitView.as_view(), name='contact_submit'),
    path('all', ContactMessageListView.as_view(), name='contact_all_legacy'),
    path('all/', ContactMessageListView.as_view(), name='contact_all'),
    path('chat/', ChatAssistantView.as_view(), name='chat_assistant'),
]
