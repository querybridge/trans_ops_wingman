from django import forms

from operations.services import filter_choices


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
