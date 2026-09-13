from django import forms

from .models import VehiclePlate, normalize_plate


class VehiclePlateForm(forms.ModelForm):
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def clean_plate(self):
        plate = self.cleaned_data["plate"]
        plate_normalized = normalize_plate(plate)
        if not plate_normalized:
            raise forms.ValidationError("Introduce una matrícula válida.")
        if self.project and VehiclePlate.objects.filter(
            project=self.project, plate_normalized=plate_normalized
        ).exists():
            raise forms.ValidationError("Esta matrícula ya está registrada en el proyecto.")
        return plate

    class Meta:
        model = VehiclePlate
        fields = ("plate", "plate_type")
        widgets = {
            "plate": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. 1234 ABC",
                    "autocomplete": "off",
                }
            ),
            "plate_type": forms.Select(attrs={"class": "form-control"}),
        }
