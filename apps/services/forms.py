from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Service, ServiceImage


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        final_attrs = {'class': 'form-control'}
        if attrs:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "category",
            "campus_location",
            "title",
            "description",
            "price",
            "is_available",
        ]


class MultipleFileField(forms.ImageField):
    """See apps/goods/forms.py::MultipleFileField for why this is needed:
    a widget-only allow_multiple_selected swap hands clean() a list, which
    breaks the standard FileField/ImageField.clean()."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ServiceImageForm(forms.ModelForm):
    """New: there was no way to attach a photo to a service (no form, no
    route). Mirrors apps/goods/forms.py::GoodImageForm."""
    image = MultipleFileField(required=False)

    class Meta:
        model = ServiceImage
        fields = ['image']