from django import forms

from .models import ContactChannel, DutyShift


class ContactChannelForm(forms.ModelForm):
    class Meta:
        model = ContactChannel
        fields = ("channel_type", "handle_or_url", "is_primary", "is_active")
        widgets = {
            "channel_type": forms.Select(attrs={"class": "form-input"}),
            "handle_or_url": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g. +639171234567 or nocturnal.cebu",
                    "autocomplete": "off",
                    "spellcheck": "false",
                }
            ),
        }


class DutyShiftStartForm(forms.ModelForm):
    class Meta:
        model = DutyShift
        fields = ("venue", "contact_channel")
        widgets = {
            "venue": forms.Select(attrs={"class": "form-input"}),
            "contact_channel": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["contact_channel"].queryset = ContactChannel.objects.filter(
                staff=user, is_active=True
            )
