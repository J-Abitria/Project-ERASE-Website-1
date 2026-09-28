import os
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from reports.integrations.instagram import InstagramGraphClient, aggregate_media_metrics
from reports.models import SocialMediaMetric


class Command(BaseCommand):
    help = "Sync Instagram post metrics from the Instagram Graph API."

    def add_arguments(self, parser):
        parser.add_argument("--since", type=date.fromisoformat, help="Only include posts on or after YYYY-MM-DD.")
        parser.add_argument("--until", type=date.fromisoformat, help="Only include posts on or before YYYY-MM-DD.")
        parser.add_argument(
            "--weekly",
            action="store_true",
            help="Sync the previous complete seven-day period (intended for a weekly scheduler).",
        )
        parser.add_argument("--dry-run", action="store_true", help="Fetch and display metrics without saving them.")

    def handle(self, *args, **options):
        if options["weekly"] and (options["since"] or options["until"]):
            raise CommandError("Use --weekly by itself, without --since or --until.")

        if options["weekly"]:
            until = timezone.localdate() - timedelta(days=1)
            since = until - timedelta(days=6)
        else:
            since = options["since"]
            until = options["until"]

        if since and until and since > until:
            raise CommandError("--since must be on or before --until.")

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
            client.get_media(since=since, until=until),
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
