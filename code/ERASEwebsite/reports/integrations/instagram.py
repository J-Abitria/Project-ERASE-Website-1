"""Small, testable client for the Instagram Graph API.

The client deliberately knows nothing about Django models. This keeps API
access and metric aggregation easy to test and leaves token/account setup to
environment variables or the management command.
"""

from collections import defaultdict
from datetime import date, datetime
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InstagramGraphAPIError(RuntimeError):
	"""Raised when Meta returns an error or an unusable response."""


class InstagramGraphClient:
	"""Client for the Instagram Graph API media and account endpoints."""

	def __init__(self, access_token, instagram_account_id, api_version="v22.0", opener=None):
		if not access_token or not instagram_account_id:
			raise ValueError("An Instagram access token and account ID are required.")
		self.access_token = access_token
		self.instagram_account_id = instagram_account_id
		self.base_url = f"https://graph.facebook.com/{api_version}"
		self.opener = opener or urlopen

	def _get(self, path, **params):
		params["access_token"] = self.access_token
		request = Request(f"{self.base_url}/{path.lstrip('/')}?{urlencode(params)}")
		try:
			with self.opener(request, timeout=30) as response:
				payload = json.load(response)
		except Exception as exc:
			raise InstagramGraphAPIError(f"Instagram Graph API request failed: {exc}") from exc

		if payload.get("error"):
			error = payload["error"]
			message = error.get("message", "Unknown Instagram Graph API error")
			raise InstagramGraphAPIError(message)
		return payload

	def get_account_followers(self):
		payload = self._get(self.instagram_account_id, fields="followers_count")
		return payload.get("followers_count")

	def get_media(self, since=None, until=None):
		"""Return media records and their available insights across all pages."""
		fields = "id,timestamp,like_count,comments_count"
		next_url = f"{self.base_url}/{self.instagram_account_id}/media?{urlencode({'fields': fields, 'access_token': self.access_token})}"
		media = []

		while next_url:
			request = Request(next_url)
			try:
				with self.opener(request, timeout=30) as response:
					payload = json.load(response)
			except Exception as exc:
				raise InstagramGraphAPIError(f"Instagram Graph API request failed: {exc}") from exc
			if payload.get("error"):
				raise InstagramGraphAPIError(payload["error"].get("message", "Unknown Instagram Graph API error"))

			for item in payload.get("data", []):
				posted_at = _parse_timestamp(item.get("timestamp"))
				if posted_at is None or (since and posted_at.date() < since) or (until and posted_at.date() > until):
					continue
				media.append(self._with_insights(item))
			next_url = payload.get("paging", {}).get("next")

		return media

	def _with_insights(self, media):
		try:
			insights = self._get(f"{media['id']}/insights", metric="reach,shares")
		except InstagramGraphAPIError:
			insights = {"data": []}
		media["insights"] = {
			item.get("name"): item.get("values", [{}])[0].get("value", 0)
			for item in insights.get("data", [])
		}
		return media


def aggregate_media_metrics(media, followers=None):
	"""Aggregate post metrics into one report row per calendar date."""
	totals = defaultdict(lambda: {"followers": followers, "post_reach": 0, "likes": 0, "shares": 0, "comments": 0})
	for item in media:
		posted_at = _parse_timestamp(item.get("timestamp"))
		if posted_at is None:
			continue
		metric = totals[posted_at.date()]
		metric["post_reach"] += _number(item.get("insights", {}).get("reach"))
		metric["likes"] += _number(item.get("like_count"))
		metric["shares"] += _number(item.get("insights", {}).get("shares"))
		metric["comments"] += _number(item.get("comments_count"))
	return dict(totals)


def _parse_timestamp(value):
	if not value:
		return None
	try:
		return datetime.fromisoformat(value.replace("Z", "+00:00"))
	except (TypeError, ValueError):
		return None


def _number(value):
	try:
		return max(0, int(value or 0))
	except (TypeError, ValueError):
		return 0