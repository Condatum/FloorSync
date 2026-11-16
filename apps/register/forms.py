from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class StaffRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. Used for official FloorSync staff communications.",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'staff@floorsync.club',
            'autocomplete': 'email',
            'spellcheck': 'false',
            'enterkeyhint': 'next',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'autocomplete': 'username',
            'autocorrect': 'off',
            'autocapitalize': 'none',
            'spellcheck': 'false',
            'enterkeyhint': 'next',
        })
        self.fields['password1'].widget.attrs.update({
            'autocomplete': 'new-password',
            'enterkeyhint': 'next',
        })
        self.fields['password2'].widget.attrs.update({
            'autocomplete': 'new-password',
            'enterkeyhint': 'done',
        })
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-input' not in current_classes:
                field.widget.attrs['class'] = f"{current_classes} form-input".strip()
