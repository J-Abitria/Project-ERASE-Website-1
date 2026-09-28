import os
from datetime import date
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import SimpleTestCase


class SyncSocialMediaCommandTests(SimpleTestCase):
    @patch.dict(os.environ, {
        'INSTAGRAM_ACCESS_TOKEN': 'test-token',
        'INSTAGRAM_ACCOUNT_ID': 'test-account',
    })
    @patch('reports.management.commands.sync_social_media.timezone.localdate')
    @patch('reports.management.commands.sync_social_media.aggregate_media_metrics', return_value={})
    @patch('reports.management.commands.sync_social_media.InstagramGraphClient')
    def test_weekly_mode_syncs_previous_complete_seven_days(
        self, client_class, aggregate_metrics, localdate
    ):
        localdate.return_value = date(2026, 9, 28)
        client_class.return_value.get_media.return_value = []
        client_class.return_value.get_account_followers.return_value = None

        call_command('sync_social_media', weekly=True, dry_run=True)

        client_class.return_value.get_media.assert_called_once_with(
            since=date(2026, 9, 21),
            until=date(2026, 9, 27),
        )
        aggregate_metrics.assert_called_once_with([], followers=None)

    @patch.dict(os.environ, {
        'INSTAGRAM_ACCESS_TOKEN': 'test-token',
        'INSTAGRAM_ACCOUNT_ID': 'test-account',
    })
    def test_weekly_mode_rejects_manual_date_bounds(self):
        with self.assertRaisesMessage(CommandError, 'Use --weekly by itself'):
            call_command(
                'sync_social_media',
                weekly=True,
                since=date(2026, 9, 1),
            )
