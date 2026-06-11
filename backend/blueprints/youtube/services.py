"""
youtube/services.py — YouTubeService: YouTube Data API v3 integration.

Fetches video metadata for course modules and caches results in the DB
to avoid repeated API calls for the same module.
"""

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL  = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeService:
    """Wraps the YouTube Data API v3 for video metadata retrieval."""

    def __init__(self):
        self._api_key = os.environ.get("YOUTUBE_API_KEY", "")

    def fetch_video_metadata(self, query: str) -> Optional[dict]:
        """
        Search YouTube for a video matching the query and return its metadata.

        Uses search.list with maxResults=1 and caches the result in the
        module record to avoid repeated API calls.

        Args:
            query: Search string composed from course title + module title.

        Returns:
            Dict with keys: video_id, title, thumbnail_url, channel_name
            None if the API call fails or quota is exceeded.
        """
        if not self._api_key:
            logger.warning("YOUTUBE_API_KEY not set — skipping video fetch")
            return None

        try:
            params = {
                "part":        "snippet",
                "q":           query,
                "type":        "video",
                "maxResults":  1,
                "key":         self._api_key,
                "relevanceLanguage": "en",
            }
            response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                logger.info(f"No YouTube results for query: {query!r}")
                return None

            item    = items[0]
            snippet = item.get("snippet", {})
            video_id = item["id"]["videoId"]

            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
            )

            return {
                "video_id":     video_id,
                "title":        snippet.get("title", ""),
                "thumbnail_url": thumbnail_url,
                "channel_name": snippet.get("channelTitle", ""),
            }

        except requests.exceptions.HTTPError as exc:
            # 403 = quota exceeded; 400 = bad API key
            logger.warning(f"YouTube API HTTP error for query {query!r}: {exc}")
            return None
        except Exception as exc:
            logger.warning(f"YouTube API call failed for query {query!r}: {exc}")
            return None

    def get_video(self, video_id: str) -> Optional[dict]:
        """
        Fetch metadata for a specific YouTube video by ID.

        Args:
            video_id: YouTube video ID (e.g. 'dQw4w9WgXcQ').

        Returns:
            Dict with video details or None on failure.
        """
        if not self._api_key:
            return None

        try:
            params = {
                "part": "snippet,contentDetails",
                "id":   video_id,
                "key":  self._api_key,
            }
            response = requests.get(YOUTUBE_VIDEO_URL, params=params, timeout=10)
            response.raise_for_status()
            data  = response.json()
            items = data.get("items", [])
            if not items:
                return None

            item    = items[0]
            snippet = item.get("snippet", {})
            thumbnails = snippet.get("thumbnails", {})

            return {
                "video_id":       video_id,
                "title":          snippet.get("title", ""),
                "description":    snippet.get("description", ""),
                "thumbnail_url":  (
                    thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url")
                ),
                "channel_name":   snippet.get("channelTitle", ""),
                "published_at":   snippet.get("publishedAt", ""),
                "duration":       item.get("contentDetails", {}).get("duration", ""),
            }
        except Exception as exc:
            logger.warning(f"YouTube get_video failed for {video_id}: {exc}")
            return None
