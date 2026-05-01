# XSTREAM — Setup in 3 steps

## Step 1 — Backend (Railway)
1. Push the `backend/` folder to GitHub
2. Railway → New Project → Deploy from GitHub repo
3. Done. Copy your Railway URL: `https://xxx.up.railway.app`

## Step 2 — Frontend
1. Open `frontend/xstream.html` in any text editor
2. Line 1 of the script: change `API_BASE` to your Railway URL
3. Open the HTML file in Chrome/Firefox

## Step 3 — Use it
| Feature | How |
|---------|-----|
| Search | Type keywords → GO (or Enter) |
| Sort/Filter | Use dropdowns in topbar |
| Load more | LOAD MORE button at bottom of sidebar |
| Video URL | Switch to "Video URL" tab → paste xhamster URL |
| Pornstar | Switch to "Pornstar" tab → paste pornstar page URL |
| Channel | Switch to "Channel" tab → paste channel page URL |
| Stream | Click any result → plays inline via HLS.js |
| Copy URL | COPY URL button in player header |
| Copy M3U8 | COPY M3U8 button — for VLC / external players |
| Download | ↓ DOWNLOAD button → shows M3U8, yt-dlp, ffmpeg commands |

## Download
The download modal gives you:
- **M3U8 URL** — open in VLC directly
- **yt-dlp command** — `pip install yt-dlp` then paste in terminal → saves MP4
- **ffmpeg command** — if you have ffmpeg installed

## Local Backend Dev
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Then set `API_BASE = 'http://localhost:8000'` in the frontend.
