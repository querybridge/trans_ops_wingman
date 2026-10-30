from django import forms

from operations.services import filter_choices

from .models import SEVERITIES, UserPreference


class ExceptionFilterForm(forms.Form):
    customer = forms.ChoiceField(required=False)
    region = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = filter_choices()
        self.fields["customer"].choices = [("", "All customers"), *choices["customers"]]
        self.fields["region"].choices = [("", "All regions"), *choices["regions"]]

    def scope(self):
        """Validated (customer_id, region); invalid input falls back to unfiltered."""
        if self.is_valid():
            return self.cleaned_data["customer"] or None, self.cleaned_data["region"] or None
        return None, None


class WorklistFilterForm(forms.Form):
    customer = forms.ChoiceField(required=False)
    regions = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)
    severities = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple, choices=SEVERITIES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = filter_choices()
        self.fields["customer"].choices = [("", "All customers"), *choices["customers"]]
        self.fields["regions"].choices = choices["regions"]

    def scope(self):
        """Validated (customer_id, regions, severities). An empty list means all; invalid input falls back to all."""
        if self.is_valid():
            d = self.cleaned_data
            return d["customer"] or None, d["regions"], d["severities"]
        return None, [], []


class PreferenceForm(forms.ModelForm):
    worklist_regions = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, label="Regions",
        help_text="Leave all unchecked to see every region.",
    )
    worklist_severities = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, choices=SEVERITIES, label="Urgency levels",
        error_messages={"required": "Choose at least one urgency level."},
    )

    class Meta:
        model = UserPreference
        fields = ["worklist_regions", "worklist_severities"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["worklist_regions"].choices = filter_choices()["regions"]
