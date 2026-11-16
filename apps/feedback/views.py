from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.shortcuts import redirect, render

from .forms import UsabilityResponseForm
from .models import UsabilityResponse

STUDY_TARGET_SUBJECTS = 15


def usability_study_view(request):
    """Public usability study submission form and empirical summary dashboard."""
    if request.method == "POST":
        form = UsabilityResponseForm(request.POST)
        if form.is_valid():
            response_obj = form.save()
            messages.success(
                request,
                f"Usability response recorded for {response_obj.participant_code}.",
            )
            return redirect("feedback:study")
        messages.error(request, "Please correct the highlighted errors before submitting.")
    else:
        form = UsabilityResponseForm()

    aggregates = UsabilityResponse.objects.aggregate(
        total_count=Count("id"),
        staff_count=Count("id", filter=Q(participant_type="STAFF")),
        patron_count=Count("id", filter=Q(participant_type="PATRON")),
        avg_sus=Avg("sus_score"),
        avg_completion_seconds=Avg("task_completion_seconds"),
        avg_clarity=Avg("clarity_rating"),
    )

    total_count = aggregates["total_count"] or 0
    progress_percent = min(round((total_count / STUDY_TARGET_SUBJECTS) * 100), 100)

    context = {
        "form": form,
        "study_target": STUDY_TARGET_SUBJECTS,
        "total_count": total_count,
        "progress_percent": progress_percent,
        "staff_count": aggregates["staff_count"] or 0,
        "patron_count": aggregates["patron_count"] or 0,
        "avg_sus": round(float(aggregates["avg_sus"]), 1) if aggregates["avg_sus"] is not None else None,
        "avg_completion_seconds": (
            round(float(aggregates["avg_completion_seconds"]), 1)
            if aggregates["avg_completion_seconds"] is not None
            else None
        ),
        "avg_clarity": (
            round(float(aggregates["avg_clarity"]), 2)
            if aggregates["avg_clarity"] is not None
            else None
        ),
        "responses": UsabilityResponse.objects.order_by("-submitted_at", "-id")[:25],
    }
    return render(request, "feedback/study.html", context)
