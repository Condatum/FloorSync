from django.core.management.base import BaseCommand

from apps.venue.seed import seed_nocturnal_cebu


class Command(BaseCommand):
    help = "Seed Nocturnal Cebu venue, Main Floor plan, zones, perks, and 10 tables."

    def handle(self, *args, **options):
        floor_plan = seed_nocturnal_cebu()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {floor_plan.venue.name} ({floor_plan.name}, "
                f"{floor_plan.canvas_width}x{floor_plan.canvas_height})."
            )
        )
