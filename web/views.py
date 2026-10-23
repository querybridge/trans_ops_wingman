from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from ai.llm import get_llm_client
from ai.status import ai_available, provider_status
from ai.workflow import run_briefing, run_explanation
from evaluation.models import EvaluationRun
from operations.rules import rule_definitions
from operations.services import (
    dashboard_metrics,
    get_shipment,
    list_exceptions,
    procedures_for_flags,
    shipment_flags,
)

from .forms import ExceptionFilterForm
from .ratelimit import ai_rate_limited


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


@require_GET
def dashboard(request):
    form = ExceptionFilterForm(request.GET or None)
    customer_id, region = form.scope()
    as_of = settings.DEMO_AS_OF
    exceptions = list_exceptions(customer_id, region, as_of)
    context = {
        "form": form,
        "metrics": dashboard_metrics(customer_id, region, as_of, exceptions),
        "exceptions": exceptions,
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
    flags = shipment_flags(shipment, settings.DEMO_AS_OF)
    context = {
        "shipment": shipment,
        "flags": flags,
        "procedure_groups": procedures_for_flags(shipment, flags, settings.DEMO_AS_OF),
        "customer_scope": customer_id or "",
    }
    template = "web/partials/shipment_detail.html" if _is_htmx(request) else "web/shipment.html"
    return render(request, template, context)


def _ai_client_or_state():
    """The live client, or a rendered honest state when AI can't run."""
    if not ai_available():
        return None, "unconfigured"
    client = get_llm_client()
    return client, (None if client else "not_implemented")


def _render_failure(request, result):
    return render(
        request,
        "web/partials/ai_state.html",
        {"state": "error", "message": " ".join(result.errors[:1]), "retry_url": request.path, "result": result},
    )


@require_POST
@ai_rate_limited
def explain_shipment(request, shipment_id):
    shipment = get_shipment(shipment_id, request.POST.get("customer") or None)
    if shipment is None:
        raise Http404("Shipment not found in the selected customer scope.")
    client, state = _ai_client_or_state()
    if state:
        return render(request, "web/partials/ai_state.html", {"state": state, "retry_url": request.path})
    # Scope is the shipment's own customer, taken from the database, not from the request or the model.
    result = run_explanation(shipment.shipment_id, shipment.customer.customer_id, settings.DEMO_AS_OF, client)
    if not result.ok:
        return _render_failure(request, result)
    return render(request, "web/partials/explanation.html", {"result": result, "x": result.output})


@require_POST
@ai_rate_limited
def generate_briefing(request):
    form = ExceptionFilterForm(request.POST)
    customer_id, region = form.scope()
    client, state = _ai_client_or_state()
    if state:
        return render(request, "web/partials/ai_state.html", {"state": state, "retry_url": request.path})
    label = " · ".join(filter(None, [
        dict(form.fields["customer"].choices).get(customer_id) if customer_id else "All customers",
        dict(form.fields["region"].choices).get(region) if region else "All regions",
    ]))
    result = run_briefing(customer_id, region, settings.DEMO_AS_OF, client, scope_label=label)
    if not result.ok:
        return _render_failure(request, result)
    return render(request, "web/partials/briefing_result.html", {"result": result, "b": result.output, "scope": {"customer": customer_id or ""}})


@require_GET
def documentation(request):
    return render(
        request,
        "web/documentation.html",
        {
            "providers": provider_status(),
            "rules": rule_definitions(),
            "evaluation_runs": EvaluationRun.objects.all()[:10],
            "latest_run": EvaluationRun.objects.first(),
        },
    )
