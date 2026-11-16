from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import UsabilityResponse


class UsabilityStudyTests(TestCase):
    def test_get_usability_study_page_is_publicly_accessible(self):
        response = self.client.get(reverse("feedback:study"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usability Study &amp; Feedback")
        self.assertContains(response, "<progress")
        self.assertContains(response, "0 / 15")

    def test_valid_post_saves_response_and_updates_summary_metrics(self):
        post_resp = self.client.post(
            reverse("feedback:study"),
            {
                "participant_code": "P01",
                "participant_type": "PATRON",
                "sus_score": "85.00",
                "task_completion_seconds": 40,
                "clarity_rating": 5,
                "comments": "Easy to spot available VIP tables.",
            },
        )
        self.assertEqual(post_resp.status_code, 302)
        self.assertEqual(UsabilityResponse.objects.count(), 1)

        saved = UsabilityResponse.objects.get(participant_code="P01")
        self.assertEqual(saved.participant_type, "PATRON")
        self.assertEqual(saved.sus_score, Decimal("85.00"))
        self.assertEqual(saved.task_completion_seconds, 40)
        self.assertEqual(saved.clarity_rating, 5)

        # Second response from staff to verify aggregate calculations
        self.client.post(
            reverse("feedback:study"),
            {
                "participant_code": "S01",
                "participant_type": "STAFF",
                "sus_score": "95.00",
                "task_completion_seconds": 20,
                "clarity_rating": 4,
                "comments": "Fast status updates.",
            },
        )

        get_resp = self.client.get(reverse("feedback:study"))
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.context["total_count"], 2)
        self.assertEqual(get_resp.context["staff_count"], 1)
        self.assertEqual(get_resp.context["patron_count"], 1)
        self.assertEqual(get_resp.context["progress_percent"], 13)
        self.assertEqual(get_resp.context["avg_sus"], 90.0)
        self.assertEqual(get_resp.context["avg_completion_seconds"], 30.0)
        self.assertEqual(get_resp.context["avg_clarity"], 4.5)
        self.assertContains(get_resp, "2 / 15")
        self.assertContains(get_resp, "P01")
        self.assertContains(get_resp, "S01")

    def test_duplicate_participant_code_is_rejected(self):
        UsabilityResponse.objects.create(
            participant_code="P01",
            participant_type="PATRON",
            sus_score=Decimal("80.00"),
            task_completion_seconds=50,
            clarity_rating=4,
        )

        post_resp = self.client.post(
            reverse("feedback:study"),
            {
                "participant_code": "P01",
                "participant_type": "STAFF",
                "sus_score": "90.00",
                "task_completion_seconds": 30,
                "clarity_rating": 5,
                "comments": "Duplicate code attempt",
            },
        )
        self.assertEqual(post_resp.status_code, 200)
        self.assertEqual(UsabilityResponse.objects.count(), 1)
        self.assertContains(post_resp, "Usability response with this Participant code already exists.")
