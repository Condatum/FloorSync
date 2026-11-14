from django.db import models


class UsabilityResponse(models.Model):
    PARTICIPANT_TYPES = [("STAFF", "Nightlife staff"), ("PATRON", "Frequent patron")]

    participant_code = models.CharField(max_length=10, unique=True)
    participant_type = models.CharField(max_length=10, choices=PARTICIPANT_TYPES)
    sus_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    task_completion_seconds = models.PositiveIntegerField(null=True, blank=True)
    clarity_rating = models.SmallIntegerField(null=True, blank=True)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.participant_code
