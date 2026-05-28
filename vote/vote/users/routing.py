from django.urls import re_path

from vote.users.consumers import ScrutinResultsConsumer

websocket_urlpatterns = [
    re_path(r"ws/scrutins/(?P<slug>[-\w]+)/results/$", ScrutinResultsConsumer.as_asgi()),
]
