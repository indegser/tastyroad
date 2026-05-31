#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_SQLITE = Path("data/tastyroad.sqlite")
DEFAULT_OUTPUT = Path("index.html")
KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class PlaceCandidate:
    name: str
    source: str
    title: str
    published_at: str
    url: str
    thumbnail_url: str
    status: str
    confidence: float


def load_candidates(sqlite_path: Path, limit: int) -> tuple[list[PlaceCandidate], str | None]:
    with sqlite3.connect(sqlite_path) as connection:
        ensure_render_schema(connection)
        rows = connection.execute(
            """
            select
              s.name as source,
              c.title,
              c.published_at,
              c.url,
              c.thumbnail_url,
              r.display_name,
              m.status,
              m.confidence
            from mentions m
            join restaurants r on r.id = m.restaurant_id
            join mention_candidates c on c.id = m.mention_candidate_id
            join sources s on s.id = c.source_id
            order by c.published_at desc, r.display_name
            limit ?
            """,
            (limit,),
        ).fetchall()
        collected_row = connection.execute(
            "select max(collected_at) from mention_candidates"
        ).fetchone()

    candidates: list[PlaceCandidate] = []
    for source, title, published_at, url, thumbnail_url, name, status, confidence in rows:
        candidates.append(
            PlaceCandidate(
                name=str(name),
                source=str(source),
                title=str(title),
                published_at=str(published_at),
                url=str(url),
                thumbnail_url=str(thumbnail_url or ""),
                status=str(status),
                confidence=float(confidence),
            )
        )

    collected_at = str(collected_row[0]) if collected_row and collected_row[0] else None
    return candidates, collected_at


def ensure_render_schema(connection: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in connection.execute("pragma table_info(mention_candidates)").fetchall()
    }
    if "thumbnail_url" not in columns:
        connection.execute(
            "alter table mention_candidates add column thumbnail_url text not null default ''"
        )


def format_datetime(value: str | None) -> str:
    if not value:
        return "알 수 없음"
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(KST).strftime("%Y. %-m. %-d. %p %-I:%M").replace(
        "AM", "오전"
    ).replace("PM", "오후")


def render_candidate(candidate: PlaceCandidate, index: int) -> str:
    thumbnail = candidate.thumbnail_url or fallback_thumbnail_url(candidate.url)
    return f"""        <li>
          <a class="video-card" href="{html.escape(candidate.url, quote=True)}">
            <img
              class="thumbnail"
              src="{html.escape(thumbnail, quote=True)}"
              alt=""
              loading="lazy"
            />
            <div class="video-info">
              <span class="index">{index:02d}</span>
              <div>
                <h2>{html.escape(candidate.title)}</h2>
                <p class="meta muted">{html.escape(candidate.source)} · 업로드 {format_datetime(candidate.published_at)}</p>
                <p class="restaurant">{html.escape(candidate.name)} · {html.escape(candidate.status)} {candidate.confidence:.2f}</p>
              </div>
            </div>
          </a>
        </li>"""


def fallback_thumbnail_url(url: str) -> str:
    if "youtu.be/" in url:
        video_id = url.rsplit("/", 1)[-1].split("?", 1)[0]
    elif "watch?v=" in url:
        video_id = url.split("watch?v=", 1)[-1].split("&", 1)[0]
    elif "/shorts/" in url:
        video_id = url.rsplit("/shorts/", 1)[-1].split("?", 1)[0]
    else:
        video_id = ""
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""


def render_page(candidates: list[PlaceCandidate]) -> str:
    items = "\n".join(
        render_candidate(candidate, index)
        for index, candidate in enumerate(candidates, start=1)
    )
    latest_published_at = candidates[0].published_at if candidates else None
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>맛집 최신 크롤링</title>
    <meta
      name="description"
      content="유튜브 RSS에서 수집한 맛집 후보를 최신순으로 보여줍니다."
    />
    <style>
      :root {{
        color-scheme: light dark;
        --bg: #ffffff;
        --fg: #171717;
        --muted: #666666;
        --line: #e6e6e6;
        --link: #0f5f7a;
      }}

      @media (prefers-color-scheme: dark) {{
        :root {{
          --bg: #111111;
          --fg: #f3f3f3;
          --muted: #a8a8a8;
          --line: #303030;
          --link: #7dd3fc;
        }}
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        background: var(--bg);
        color: var(--fg);
        font-family:
          -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI",
          sans-serif;
        line-height: 1.55;
      }}

      main {{
        width: min(680px, 100%);
        margin: 0 auto;
        padding: 28px 16px 40px;
      }}

      header {{
        margin-bottom: 32px;
      }}

      h1 {{
        margin: 0 0 10px;
        font-size: clamp(2rem, 5vw, 3rem);
        line-height: 1.12;
        letter-spacing: 0;
      }}

      p {{
        margin: 0;
      }}

      .muted {{
        color: var(--muted);
      }}

      .summary {{
        margin-top: 8px;
        font-size: 1rem;
      }}

      ol {{
        list-style: none;
        margin: 0;
        padding: 0;
      }}

      li {{
        padding: 0 0 28px;
      }}

      .index {{
        display: block;
        width: 36px;
        flex: 0 0 36px;
        padding-top: 2px;
        color: var(--muted);
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.86rem;
      }}

      a {{
        display: block;
        color: inherit;
        text-decoration: none;
      }}

      a:hover h2 {{
        color: var(--link);
        text-decoration: underline;
      }}

      h2 {{
        display: -webkit-box;
        margin: 0 0 5px;
        overflow-wrap: anywhere;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        font-size: 1.04rem;
        line-height: 1.34;
        letter-spacing: 0;
      }}

      .thumbnail {{
        display: block;
        width: 100%;
        aspect-ratio: 16 / 9;
        object-fit: cover;
        border-radius: 8px;
        background: var(--line);
      }}

      .video-info {{
        display: flex;
        gap: 10px;
        padding-top: 10px;
      }}

      .meta,
      .restaurant {{
        font-size: 0.91rem;
        line-height: 1.42;
      }}

      .restaurant {{
        margin-top: 2px;
        overflow-wrap: anywhere;
      }}

      @media (min-width: 720px) {{
        main {{
          padding-top: 44px;
        }}

        li {{
          padding-bottom: 34px;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <p class="muted">최신 영상: {format_datetime(latest_published_at)}</p>
        <h1>맛집 최신 크롤링</h1>
        <p class="summary muted">
          유튜브 출처에서 검증한 식당을 영상 발행일 최신순으로
          정리했습니다.
        </p>
      </header>

      <ol>
{items}
      </ol>
    </main>
  </body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render tastyroad static HTML from SQLite data.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    candidates, _collected_at = load_candidates(args.sqlite, args.limit)
    args.output.write_text(render_page(candidates), encoding="utf-8")
    print(f"Rendered {len(candidates)} candidates -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
