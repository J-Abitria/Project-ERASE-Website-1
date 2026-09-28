from datetime import date

from django.test import SimpleTestCase

from reports.integrations.instagram import aggregate_media_metrics


class InstagramMetricAggregationTests(SimpleTestCase):
    def test_aggregates_post_metrics_by_calendar_date(self):
        media = [
            {
                "timestamp": "2026-09-20T10:00:00+0000",
                "like_count": 12,
                "comments_count": 3,
                "insights": {"reach": 100, "shares": 4},
            },
            {
                "timestamp": "2026-09-20T18:00:00+0000",
                "like_count": 8,
                "comments_count": 2,
                "insights": {"reach": 50, "shares": 1},
            },
        ]

        result = aggregate_media_metrics(media, followers=250)

        self.assertEqual(
            result[date(2026, 9, 20)],
            {
                "followers": 250,
                "post_reach": 150,
                "likes": 20,
                "shares": 5,
                "comments": 5,
            },
        )
