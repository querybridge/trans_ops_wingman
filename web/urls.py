from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "web"

urlpatterns = [
    path("", views.worklist_view, name="worklist"),
    path("exceptions/", views.dashboard, name="dashboard"),
    path("shipments/<str:shipment_id>/", views.shipment_detail, name="shipment_detail"),
    path("shipments/<str:shipment_id>/explain/", views.explain_shipment, name="explain_shipment"),
    path("worklist/", RedirectView.as_view(pattern_name="web:worklist", query_string=True)),
    path("worklist/<str:shipment_id>/recommend/", views.recommend_next_step, name="recommend_next_step"),
    path("settings/", views.user_settings, name="settings"),
    path("briefing/", views.generate_briefing, name="generate_briefing"),
    path("documentation/", views.documentation, name="documentation"),
    path("technology/", views.technology, name="technology"),
]
