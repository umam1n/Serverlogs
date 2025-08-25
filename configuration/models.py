# FILE: configuration/models.py

from django.db import models

class SiteSettings(models.Model):
    camera_verification_enabled = models.BooleanField(
        default=True,
        help_text="Globally enable or disable all camera functions (enrollment, check-in, etc.)."
    )
    # --- ADD THIS NEW FIELD ---
    location_verification_enabled = models.BooleanField(
        default=True,
        help_text="Globally enable or disable the GPS/location check during check-in."
    )
    # --- END ADDITION ---

    def __str__(self):
        return "Site-wide Settings"

    class Meta:
        verbose_name_plural = "Site Settings"