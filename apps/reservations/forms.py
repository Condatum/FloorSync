from django import forms

from apps.venue.models import Table

from .models import Reservation


class ReservationForm(forms.ModelForm):
    reserved_for = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-input",
                "autocomplete": "off",
                "enterkeyhint": "next",
            },
            format="%Y-%m-%dT%H:%M",
        ),
    )

    class Meta:
        model = Reservation
        fields = (
            "table",
            "guest_name",
            "guest_contact",
            "party_size",
            "reserved_for",
            "deposit_amount",
            "payment_verified",
            "status",
            "remarks",
        )
        widgets = {
            "table": forms.Select(
                attrs={
                    "class": "form-input",
                    "autocomplete": "off",
                }
            ),
            "guest_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g. Marco Reyes",
                    "autocomplete": "name",
                    "enterkeyhint": "next",
                }
            ),
            "guest_contact": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g. +639171234567 or @marco",
                    "autocomplete": "tel",
                    "enterkeyhint": "next",
                }
            ),
            "party_size": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "min": "1",
                    "max": "50",
                    "autocomplete": "off",
                    "enterkeyhint": "next",
                }
            ),
            "deposit_amount": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "min": "0",
                    "step": "0.01",
                    "autocomplete": "off",
                    "enterkeyhint": "next",
                }
            ),
            "payment_verified": forms.CheckboxInput(),
            "status": forms.Select(
                attrs={
                    "class": "form-input",
                    "autocomplete": "off",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 2,
                    "placeholder": "Bottle requests, arrival notes, or special instructions",
                    "autocomplete": "off",
                    "enterkeyhint": "done",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["table"].queryset = Table.objects.select_related("zone").order_by(
            "zone__sort_order", "code"
        )
