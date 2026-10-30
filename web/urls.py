from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("shipments/<str:shipment_id>/", views.shipment_detail, name="shipment_detail"),
    path("shipments/<str:shipment_id>/explain/", views.explain_shipment, name="explain_shipment"),
    path("worklist/", views.worklist_view, name="worklist"),
    path("worklist/<str:shipment_id>/recommend/", views.recommend_next_step, name="recommend_next_step"),
    path("briefing/", views.generate_briefing, name="generate_briefing"),
    path("documentation/", views.documentation, name="documentation"),
]
