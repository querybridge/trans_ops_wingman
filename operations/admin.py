from django.contrib import admin

from .models import Customer, DispatchNote, ProcedureChunk, ProcedureDocument, Shipment, ShipmentEvent


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0


class DispatchNoteInline(admin.TabularInline):
    model = DispatchNote
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["customer_id", "name"]


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ["shipment_id", "customer", "region", "status", "delivery_window_end", "delivered_at"]
    list_filter = ["customer", "region", "status"]
    search_fields = ["shipment_id", "source_record_id"]
    inlines = [ShipmentEventInline, DispatchNoteInline]


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "shipment", "event_type", "occurred_at"]
    list_filter = ["event_type"]
    search_fields = ["event_id", "shipment__shipment_id"]


@admin.register(DispatchNote)
class DispatchNoteAdmin(admin.ModelAdmin):
    list_display = ["note_id", "shipment", "author_role", "noted_at"]
    search_fields = ["note_id", "shipment__shipment_id", "text"]


class ProcedureChunkInline(admin.TabularInline):
    model = ProcedureChunk
    extra = 0


@admin.register(ProcedureDocument)
class ProcedureDocumentAdmin(admin.ModelAdmin):
    list_display = ["document_id", "version", "title", "customer", "issue_type", "effective_from", "effective_to"]
    list_filter = ["issue_type", "customer"]
    inlines = [ProcedureChunkInline]
