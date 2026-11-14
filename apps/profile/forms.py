from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("full_name", "bio", "profile_image")
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Full name",
            }),
            "bio": forms.Textarea(attrs={
                "class": "form-input",
                "placeholder": "A short bio for your staff profile",
                "rows": 4,
            }),
        }
