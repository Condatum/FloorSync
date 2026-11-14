from django import forms
from django.contrib.auth.forms import AuthenticationForm


class StaffLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter staff username',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter password',
        })
