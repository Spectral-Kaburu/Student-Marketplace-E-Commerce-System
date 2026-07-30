from django.db import models

from django.conf import settings

from django.core.exceptions import ValidationError

from apps.common.image_processing import process_image, processed_filename



class Good(models.Model):

    CONDITION_CHOICES = [

        ('new', 'New'),

        ('used', 'Used'),

    ]

    STATUS_CHOICES = [

        ('available', 'Available'),

        ('unavailable', 'Unavailable'),

    ]



    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    category = models.ForeignKey('catalog.Category', on_delete=models.CASCADE)

    title = models.CharField(max_length=150)

    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)



    class Meta:

        constraints = [

            models.CheckConstraint(

                check=models.Q(price__gte=0),

                name='price_must_be_positive'

            ),

            models.CheckConstraint(

                check=models.Q(condition__in=['new', 'used']),

                name='valid_condition'

            ),

            models.CheckConstraint(

                check=models.Q(status__in=['available', 'unavailable']),

                name='valid_status'

            ),

        ]



    def __str__(self):

        return self.title





class GoodImage(models.Model):

    good = models.ForeignKey(Good, on_delete=models.CASCADE, related_name='images')

    # Real file upload (switched from URLField per Step 2a) so sellers can
    # upload an actual photo during the live demo instead of pasting a link.
    # Nullable/blankable: we allow listings without photos.
    image = models.ImageField(upload_to='goods/%Y/%m/', null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)



    def clean(self):

        # Enforces the max 15 images rule before saving.
        # Guarded on self.good_id: GoodCreateView/GoodUpdateView call
        # image_form.is_valid() before the Good is created/assigned, which
        # was crashing every image upload with RelatedObjectDoesNotExist.
        # The cap is still enforced -- save() re-runs clean() once `good`
        # is actually set, right before the row is written.
        if self.good_id and self.good.images.count() >= 15 and not self.pk:

            raise ValidationError("A maximum of 15 images is allowed per good.")



    def save(self, *args, **kwargs):

        # Force the clean method to run on save

        self.clean()

        # Only process a freshly-uploaded file, not an already-committed
        # one -- otherwise every unrelated re-save (e.g. admin editing
        # uploaded_at, or a future bulk update) would re-crop the image
        # from its own already-cropped output and degrade it through
        # repeated JPEG re-compression.
        if self.image and not self.image._committed:
            processed = process_image(self.image)
            if processed:
                new_name = processed_filename(self.image.name)
                self.image.save(new_name, processed, save=False)

        super().save(*args, **kwargs)



    def __str__(self):

        return f"Image for {self.good.title}" 

