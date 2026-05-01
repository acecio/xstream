from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Literal
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="XStream API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy client (initialized once) ──────────────────────
_client = None

def get_client():
    global _client
    if _client is None:
        from xhamster_api import Client
        _client = Client()
        logger.info("xhamster_api Client initialized")
    return _client

# ── Serializers ─────────────────────────────────────────
def video_dict(v) -> dict:
    try:
        return {
            "type": "video",
            "url": v.url,
            "title": _safe(lambda: v.title),
            "thumbnail": _safe(lambda: v.thumbnail),
            "pornstars": _safe(lambda: v.pornstars, []),
            "m3u8": _safe(lambda: v.m3u8_base_url),
        }
    except Exception as e:
        logger.warning(f"video_dict fallback for {getattr(v,'url','?')}: {e}")
        return {"type": "video", "url": getattr(v,'url',''), "title": "", "thumbnail": "", "pornstars": [], "m3u8": ""}

def short_dict(s) -> dict:
    try:
        return {
            "type": "short",
            "url": s.url,
            "title": _safe(lambda: s.title),
            "author": _safe(lambda: s.author),
            "likes": _safe(lambda: s.likes, 0),
            "m3u8": _safe(lambda: s.m3u8_base_url),
        }
    except Exception as e:
        logger.warning(f"short_dict fallback: {e}")
        return {"type": "short", "url": getattr(s,'url',''), "title": "", "author": "", "likes": 0, "m3u8": ""}

def _safe(fn, default=None):
    try:
        v = fn()
        return v if v is not None else default
    except Exception:
        return default

# ── Routes ───────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.1.0"}

@app.get("/")
def root():
    return {"message": "XStream API", "docs": "/docs", "health": "/health"}

@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    pages: int = Query(2, ge=1, le=5),
    sort_by: Optional[Literal["views", "newest", "best", "longest"]] = None,
    category: Optional[str] = None,
    min_duration: Optional[Literal["2", "5", "10", "30", "40"]] = None,
    quality: Optional[Literal["720p", "1080p", "2160p"]] = None,
):
    def _run():
        c = get_client()
        kwargs = {"query": q, "pages": pages}
        if sort_by:    kwargs["sort_by"] = sort_by
        if category:   kwargs["category"] = category
        if min_duration: kwargs["min_duration"] = min_duration
        if quality:    kwargs["minimum_quality"] = quality

        results = []
        try:
            for v in c.search_videos(**kwargs):
                d = video_dict(v)
                if d.get("url"):
                    results.append(d)
        except Exception as e:
            logger.error(f"Search generator error: {e}")
        return results

    try:
        results = await asyncio.get_event_loop().run_in_executor(None, _run)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"/search error: {e}")
        raise HTTPException(500, str(e))


@app.get("/video")
async def get_video(url: str = Query(...)):
    def _run():
        c = get_client()
        return video_dict(c.get_video(url))
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        logger.error(f"/video error: {e}")
        raise HTTPException(500, str(e))


@app.get("/short")
async def get_short(url: str = Query(...)):
    def _run():
        c = get_client()
        return short_dict(c.get_short(url))
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        logger.error(f"/short error: {e}")
        raise HTTPException(500, str(e))


@app.get("/pornstar")
async def get_pornstar(url: str = Query(...), pages: int = Query(2, ge=1, le=5)):
    def _run():
        c = get_client()
        ps = c.get_pornstar(url)
        videos = []
        try:
            for v in ps.videos(pages=pages):
                d = video_dict(v)
                if d.get("url"):
                    videos.append(d)
        except Exception as e:
            logger.warning(f"pornstar videos error: {e}")
        return {
            "name":         _safe(lambda: ps.name, "Unknown"),
            "subscribers":  _safe(lambda: ps.subscribers_count, "0"),
            "video_count":  _safe(lambda: ps.videos_count, "0"),
            "total_views":  _safe(lambda: ps.total_views_count, "0"),
            "avatar":       _safe(lambda: ps.avatar_url),
            "videos":       videos,
        }
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        logger.error(f"/pornstar error: {e}")
        raise HTTPException(500, str(e))


@app.get("/channel")
async def get_channel(url: str = Query(...), pages: int = Query(2, ge=1, le=5)):
    def _run():
        c = get_client()
        ch = c.get_channel(url)
        videos = []
        try:
            for v in ch.videos(pages=pages):
                d = video_dict(v)
                if d.get("url"):
                    videos.append(d)
        except Exception as e:
            logger.warning(f"channel videos error: {e}")
        return {
            "name":        _safe(lambda: ch.name, "Unknown"),
            "subscribers": _safe(lambda: ch.subscribers_count, "0"),
            "video_count": _safe(lambda: ch.videos_count, "0"),
            "total_views": _safe(lambda: ch.total_views_count, "0"),
            "videos":      videos,
        }
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        logger.error(f"/channel error: {e}")
        raise HTTPException(500, str(e))


@app.get("/m3u8")
async def get_m3u8(url: str = Query(...)):
    """Just the M3U8 stream URL for a given video page URL"""
    def _run():
        c = get_client()
        v = c.get_video(url)
        return {
            "m3u8":  _safe(lambda: v.m3u8_base_url),
            "title": _safe(lambda: v.title),
        }
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        raise HTTPException(500, str(e))
