from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from PythonModule import Session,Suno

app = FastAPI(title="PyScrapper Suno Local Server", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"


class SunoDownloadRequest(BaseModel):
    url: str = Field(..., min_length=10)
    mediatype: str = ".mp3"  # ".mp3", ".mp4" (".wav" ist bei dir evtl buggy)


class SunoDownloadResponse(BaseModel):
    ok: bool
    file_path: str | None = None
    error: str | None = None


@app.get("/health")
def health():
    return {"ok": True, "version": app.version}


@app.post("/suno/download", response_model=SunoDownloadResponse)
def suno_download(req: SunoDownloadRequest):
    try:
        if req.mediatype not in (".mp3", ".mp4", ".wav"):
            raise HTTPException(status_code=400, detail="mediatype must be .mp3, .mp4 or .wav")

        # Download-Ordner sicherstellen
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

        # Deine bestehende Implementierung benutzen:
        ses = Session.Session()
        Suno.download(
            session=ses,
            url=req.url,
            mediatype=req.mediatype,
            out_path=str(DOWNLOADS_DIR),
        )

        identifier = req.url.replace("https://suno.com/song/", "").strip()
        out_file = (DOWNLOADS_DIR / f"{identifier}{req.mediatype}").resolve()

        if not out_file.exists():
            # falls Suno.download intern anders speichert, siehst du das sofort
            raise RuntimeError(f"Download finished but file not found: {out_file}")

        return SunoDownloadResponse(ok=True, file_path=str(out_file))

    except HTTPException:
        raise
    except Exception as e:
        return SunoDownloadResponse(ok=False, error=str(e))