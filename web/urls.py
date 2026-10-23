from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("shipments/<str:shipment_id>/", views.shipment_detail, name="shipment_detail"),
    path("shipments/<str:shipment_id>/explain/", views.explain_shipment, name="explain_shipment"),
    path("briefing/", views.generate_briefing, name="generate_briefing"),
    path("about/", views.about, name="about"),
]
