import os
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from reports.integrations.instagram import InstagramGraphClient, aggregate_media_metrics
from reports.models import SocialMediaMetric


class Command(BaseCommand):
    help = "Sync daily Instagram post metrics from the Instagram Graph API."

    def add_arguments(self, parser):
        parser.add_argument("--since", type=date.fromisoformat, help="Only include posts on or after YYYY-MM-DD.")
        parser.add_argument("--until", type=date.fromisoformat, help="Only include posts on or before YYYY-MM-DD.")
        parser.add_argument("--dry-run", action="store_true", help="Fetch and display metrics without saving them.")

    def handle(self, *args, **options):
        access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        if not access_token or not account_id:
            raise CommandError("Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID before syncing Instagram.")

        client = InstagramGraphClient(
            access_token=access_token,
            instagram_account_id=account_id,
            api_version=os.getenv("META_GRAPH_API_VERSION", "v22.0"),
        )
        metrics = aggregate_media_metrics(
            client.get_media(since=options["since"], until=options["until"]),
            followers=client.get_account_followers(),
        )

        for metric_date, values in sorted(metrics.items()):
            defaults = {**values, "notes": "Synced from Instagram Graph API."}
            if options["dry_run"]:
                self.stdout.write(f"{metric_date}: {defaults}")
                continue
            SocialMediaMetric.objects.update_or_create(
                platform="instagram",
                date=metric_date,
                defaults=defaults,
            )
            self.stdout.write(self.style.SUCCESS(f"Synced Instagram metrics for {metric_date}."))

        self.stdout.write(f"Processed {len(metrics)} Instagram day(s).")
