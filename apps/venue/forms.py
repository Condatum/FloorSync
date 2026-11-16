from django import forms

from .models import Perk, Table, TablePerk, Zone


class TableForm(forms.ModelForm):
    perks = forms.ModelMultipleChoiceField(
        queryset=Perk.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Table
        fields = (
            "zone",
            "code",
            "label",
            "capacity",
            "min_spend",
            "shape",
            "pos_x",
            "pos_y",
            "width",
            "height",
            "status",
            "is_visible",
            "perks",
        )
        widgets = {
            "zone": forms.Select(attrs={"class": "form-input"}),
            "code": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. VIP-06"}),
            "label": forms.TextInput(attrs={"class": "form-input", "placeholder": "Optional display label"}),
            "capacity": forms.NumberInput(attrs={"class": "form-input", "min": "1", "max": "50"}),
            "min_spend": forms.NumberInput(attrs={"class": "form-input", "min": "0", "step": "100"}),
            "shape": forms.Select(attrs={"class": "form-input"}),
            "pos_x": forms.NumberInput(attrs={"class": "form-input", "min": "0", "max": "1200", "step": "1"}),
            "pos_y": forms.NumberInput(attrs={"class": "form-input", "min": "0", "max": "800", "step": "1"}),
            "width": forms.NumberInput(attrs={"class": "form-input", "min": "30", "max": "600", "step": "1"}),
            "height": forms.NumberInput(attrs={"class": "form-input", "min": "30", "max": "600", "step": "1"}),
            "status": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, floor_plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        if floor_plan is not None:
            self.fields["zone"].queryset = Zone.objects.filter(floor_plan=floor_plan).order_by(
                "sort_order", "name"
            )
        if self.instance and self.instance.pk and not self.is_bound:
            self.initial["perks"] = self.instance.perks.values_list("pk", flat=True)

    def save(self, commit=True):
        table = super().save(commit=False)
        if commit:
            table.save()
            selected_perks = list(self.cleaned_data.get("perks") or [])
            selected_ids = {p.pk for p in selected_perks}
            TablePerk.objects.filter(table=table).exclude(perk_id__in=selected_ids).delete()
            for perk in selected_perks:
                TablePerk.objects.get_or_create(table=table, perk=perk)
        return table
