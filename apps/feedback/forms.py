from django import forms

from .models import UsabilityResponse


class UsabilityResponseForm(forms.ModelForm):
    sus_score = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "min": "0",
                "max": "100",
                "step": "0.5",
                "inputmode": "decimal",
                "enterkeyhint": "next",
                "placeholder": "0 – 100",
                "autocomplete": "off",
            }
        ),
    )
    task_completion_seconds = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "min": "0",
                "step": "1",
                "inputmode": "numeric",
                "enterkeyhint": "next",
                "placeholder": "e.g. 45",
                "autocomplete": "off",
            }
        ),
    )
    clarity_rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "min": "1",
                "max": "5",
                "step": "1",
                "inputmode": "numeric",
                "enterkeyhint": "next",
                "placeholder": "1 – 5",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = UsabilityResponse
        fields = (
            "participant_code",
            "participant_type",
            "sus_score",
            "task_completion_seconds",
            "clarity_rating",
            "comments",
        )
        widgets = {
            "participant_code": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g. P01",
                    "maxlength": "10",
                    "autocomplete": "off",
                    "autocorrect": "off",
                    "autocapitalize": "none",
                    "spellcheck": "false",
                    "enterkeyhint": "next",
                }
            ),
            "participant_type": forms.Select(
                attrs={
                    "class": "form-input",
                    "autocomplete": "off",
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 3,
                    "placeholder": "Share navigation friction points, clarity notes, or suggestions",
                    "enterkeyhint": "done",
                }
            ),
        }

    def clean_participant_code(self):
        return self.cleaned_data["participant_code"].strip()
