from django import forms
from django.forms.widgets import ClearableFileInput
from apps.goods.models import Good, GoodImage


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        final_attrs = {'class': 'form-control'}
        if attrs:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)


class GoodForm(forms.ModelForm):
     class Meta:
         model = Good
         fields = ['title', 'description', 'price', 'category', 'condition']
         ...

class MultipleFileField(forms.ImageField):
    """FileField/ImageField.clean() only knows how to handle a single
    UploadedFile. When the widget has allow_multiple_selected=True,
    request.FILES.getlist(name) hands clean() a *list* instead, which
    blows up in FileField.to_python() (AttributeError on .name/.size,
    surfaced as "No file was submitted. Check the encoding type on the
    form."). This subclass runs the normal single-file clean() over
    each item in the list. Mirrors Django's documented pattern for
    multi-file uploads."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class GoodImageForm(forms.ModelForm):
    # Declared explicitly (not via Meta.widgets) because we need Django
    # to use our custom Field class, not just our custom widget --
    # Meta.widgets can only swap the widget, and ModelForm would still
    # generate a plain ImageField otherwise.
    image = MultipleFileField(required=False)

    class Meta:
        model = GoodImage
        fields = ['image']

        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }
        fields = ['image']