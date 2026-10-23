from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from ai.status import ai_available, provider_status
from evaluation.models import EvaluationRun
from operations.services import dashboard_metrics, get_shipment, list_exceptions

from .forms import ExceptionFilterForm
from .ratelimit import ai_rate_limited


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


@require_GET
def dashboard(request):
    form = ExceptionFilterForm(request.GET or None)
    customer_id, region = form.scope()
    as_of = settings.DEMO_AS_OF
    context = {
        "form": form,
        "metrics": dashboard_metrics(customer_id, region, as_of),
        "exceptions": list_exceptions(customer_id, region, as_of),
        "scope": {"customer": customer_id or "", "region": region or ""},
    }
    template = "web/partials/exception_queue.html" if _is_htmx(request) else "web/dashboard.html"
    return render(request, template, context)


@require_GET
def shipment_detail(request, shipment_id):
    customer_id = request.GET.get("customer") or None
    shipment = get_shipment(shipment_id, customer_id)
    if shipment is None:
        raise Http404("Shipment not found in the selected customer scope.")
    context = {"shipment": shipment, "customer_scope": customer_id or ""}
    template = "web/partials/shipment_detail.html" if _is_htmx(request) else "web/shipment.html"
    return render(request, template, context)


@require_POST
@ai_rate_limited
def explain_shipment(request, shipment_id):
    customer_id = request.POST.get("customer") or None
    if get_shipment(shipment_id, customer_id) is None:
        raise Http404("Shipment not found in the selected customer scope.")
    # The LangChain workflow is not wired yet; report that honestly instead of faking output.
    state = "not_implemented" if ai_available() else "unconfigured"
    return render(request, "web/partials/ai_state.html", {"state": state, "retry_url": request.path})


@require_POST
@ai_rate_limited
def generate_briefing(request):
    state = "not_implemented" if ai_available() else "unconfigured"
    return render(request, "web/partials/ai_state.html", {"state": state, "retry_url": request.path})


@require_GET
def documentation(request):
    return render(
        request,
        "web/documentation.html",
        {"providers": provider_status(), "evaluation_runs": EvaluationRun.objects.all()[:10]},
    )
