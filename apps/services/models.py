from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.catalog.models import Category, CampusLocation
from apps.common.image_processing import process_image, processed_filename


class Service(models.Model):
    id = models.BigAutoField(primary_key=True)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="services"
    )
    campus_location = models.ForeignKey(
        CampusLocation,
        on_delete=models.CASCADE,
        related_name="services"
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class ServiceImage(models.Model):
    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="images"
    )
    # Nullable/blankable: allow services without photos
    image = models.ImageField(upload_to="services/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforce max 15 images per service (mirrors GoodImage)
        if self.service_id and self.service.images.count() >= 15 and not self.pk:
            raise ValidationError("A maximum of 15 images is allowed per service.")

    def save(self, *args, **kwargs):
        # NOTE: this override didn't exist before -- clean() was defined
        # but nothing ever called it, so the 15-image cap was silently
        # unenforced. Mirrors GoodImage.save() exactly.
        self.clean()

        if self.image and not self.image._committed:
            processed = process_image(self.image)
            if processed:
                new_name = processed_filename(self.image.name)
                self.image.save(new_name, processed, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.service.title}"
