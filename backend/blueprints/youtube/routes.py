"""
youtube/routes.py — YouTube search and video metadata endpoints.

Endpoints:
    GET /api/v1/youtube/search?q=<query>  — Search YouTube videos
    GET /api/v1/youtube/video/<video_id>  — Get single video metadata
"""

from flask import request
from flask_jwt_extended import jwt_required

from ...app import error_response, success_response
from . import youtube_bp
from .services import YouTubeService

_yt = YouTubeService()


@youtube_bp.route("/search", methods=["GET"])
@jwt_required()
def search():
    """
    Search YouTube Data API for videos matching a query string.

    Query params:
        q (str): Search query (required)

    Returns:
        200: { results: [...] }
        400: Missing query parameter
        503: YouTube API unavailable
    """
    query = request.args.get("q", "").strip()
    if not query:
        return error_response(400, "BAD_REQUEST", "Query parameter 'q' is required.")

    result = _yt.fetch_video_metadata(query)
    if result is None:
        # Graceful fallback — return empty results rather than an error
        return success_response({"results": []})

    return success_response({"results": [result]})


@youtube_bp.route("/video/<video_id>", methods=["GET"])
@jwt_required()
def get_video(video_id):
    """
    Return metadata for a specific YouTube video by ID.

    Path param:
        video_id (str): YouTube video ID

    Returns:
        200: { video }
        404: Video not found
    """
    result = _yt.get_video(video_id)
    if result is None:
        return error_response(404, "NOT_FOUND", "Video not found or YouTube API unavailable.")

    return success_response({"video": result})
