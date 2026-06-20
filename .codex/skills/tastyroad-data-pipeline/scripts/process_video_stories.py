#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collect_youtube import DEFAULT_SQLITE
from pipeline_schema import ensure_pipeline_schema


DEFAULT_LANGUAGES = ("ko", "en")
DEFAULT_INPUT = Path("data/story_reviews/video_story_reviews.json")
DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS = 0.0
DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS = 3
DISALLOWED_STORY_REVIEWER = "codex-generated-from-transcript"
STORY_QUALITY_POLICY_VERSION = "story-quality-v3"
MIN_STORY_INTRO_CHARS = 240
MIN_TASTING_FLOW_CHARS = 180
MIN_TASTING_ORDER_ITEMS = 4
MIN_TRANSCRIPT_SUPPORT_ITEMS = 3
GENERIC_STORY_PATTERNS = (
    "자막 기준으로 영상은",
    "같은 단서를 따라가며",
    "왜 이 장소가 한 끼 후보가 되는지",
    "지도에 찍힌 장소 정보뿐 아니라",
    "시식 흐름은 먼저",
    "중심으로 메뉴의 첫인상을 잡는 데서 시작한다",
    "마지막에는 이 식당이 어떤 상황에서 선택할 만한지",
    "가게 쪽 이야기도 선명하다",
    "이야기도 선명하다",
    "쪽에 가깝다",
    "매력으로 남는다",
    "성격을 비교한다",
)
PUBLIC_STORY_PROVENANCE_PATTERNS = (
    "설명란",
    "영상 설명",
    "메타데이터",
    "metadata",
    "상호",
    "주소",
    "네이버",
    "지도 링크",
    "링크가",
    "식당정보",
    "출처",
    "직접 적혀",
)
REQUIRED_CRITIC_CHECKS = (
    "tasting_order_present",
    "tasting_order_matches_transcript",
    "host_reason_specific",
    "store_context_specific",
    "plain_korean",
    "clear_subjects",
    "no_duplicate_context",
    "no_generic_phrasing",
)
MIN_STORY_CRITIC_ROUNDS = 3
LOCAL_ENV_PATH = Path.cwd() / ".env.local"


@dataclass(frozen=True)
class TranscriptPayload:
    language_code: str
    language: str
    is_generated: bool
    segments: list[dict[str, Any]]
    text: str


@dataclass(frozen=True)
class StoryProcessResult:
    fetched_transcript_count: int
    applied_review_count: int


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_local_env(path: Path = LOCAL_ENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def comma_separated_env(name: str) -> list[str] | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def int_env(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    return int(value)


def transcript_proxy_config() -> Any | None:
    load_local_env()
    webshare_username = os.environ.get("WEBSHARE_PROXY_USERNAME", "").strip()
    webshare_password = os.environ.get("WEBSHARE_PROXY_PASSWORD", "").strip()
    if webshare_username and webshare_password:
        from youtube_transcript_api.proxies import WebshareProxyConfig

        return WebshareProxyConfig(
            proxy_username=webshare_username,
            proxy_password=webshare_password,
            filter_ip_locations=comma_separated_env("WEBSHARE_PROXY_LOCATIONS"),
            retries_when_blocked=int_env("WEBSHARE_PROXY_RETRIES_WHEN_BLOCKED", 10),
            domain_name=os.environ.get("WEBSHARE_PROXY_DOMAIN", "p.webshare.io").strip()
            or "p.webshare.io",
            proxy_port=int_env("WEBSHARE_PROXY_PORT", 80),
        )

    http_proxy = os.environ.get("YT_TRANSCRIPT_HTTP_PROXY", "").strip()
    https_proxy = os.environ.get("YT_TRANSCRIPT_HTTPS_PROXY", "").strip()
    if http_proxy or https_proxy:
        from youtube_transcript_api.proxies import GenericProxyConfig

        return GenericProxyConfig(http_url=http_proxy or None, https_url=https_proxy or None)

    return None


def fetch_transcript(video_id: str, languages: tuple[str, ...]) -> TranscriptPayload:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi(proxy_config=transcript_proxy_config())
    transcript_list = api.list(video_id)
    transcript = transcript_list.find_transcript(list(languages))
    fetched = transcript.fetch()
    segments = normalize_segments(fetched)
    text = " ".join(segment["text"] for segment in segments).strip()
    return TranscriptPayload(
        language_code=str(transcript.language_code),
        language=str(transcript.language),
        is_generated=bool(transcript.is_generated),
        segments=segments,
        text=text,
    )


def is_youtube_block_error(error: Exception | str) -> bool:
    message = str(error)
    block_markers = (
        "YouTube is blocking requests from your IP",
        "RequestBlocked",
        "IpBlocked",
        "IP block",
    )
    return any(marker in message for marker in block_markers)


def normalize_segments(fetched: Any) -> list[dict[str, Any]]:
    if hasattr(fetched, "to_raw_data"):
        raw_segments = fetched.to_raw_data()
    else:
        raw_segments = fetched

    segments: list[dict[str, Any]] = []
    for segment in raw_segments:
        if hasattr(segment, "__dict__") and not isinstance(segment, dict):
            segment = segment.__dict__
        text = " ".join(str(segment.get("text", "")).replace("\n", " ").split())
        if not text:
            continue
        segments.append(
            {
                "text": text,
                "start": float(segment.get("start", 0)),
                "duration": float(segment.get("duration", 0)),
            }
        )
    return segments


def reviewed_restaurant_rows(
    connection: sqlite3.Connection,
    *,
    video_id: str | None = None,
    missing_transcript_only: bool = False,
) -> list[sqlite3.Row]:
    sql = """
        select
          v.video_id,
          v.source,
          v.title,
          v.reviewed_restaurant_names
        from video_pipeline_status v
        left join video_transcripts t on t.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
    """
    params: list[Any] = []
    if video_id:
        sql += " and v.video_id = ?"
        params.append(video_id)
    if missing_transcript_only:
        sql += " and t.external_id is null"
    sql += " order by v.published_at desc, v.youtube_video_id desc"
    return list(connection.execute(sql, params).fetchall())


def upsert_transcript(
    connection: sqlite3.Connection,
    video_id: str,
    transcript: TranscriptPayload,
    fetched_at: str,
) -> None:
    connection.execute(
        """
        insert into video_transcripts (
          external_id,
          language_code,
          language,
          is_generated,
          transcript_json,
          transcript_text,
          fetched_at
        )
        values (?, ?, ?, ?, ?, ?, ?)
        on conflict(external_id) do update set
          language_code = excluded.language_code,
          language = excluded.language,
          is_generated = excluded.is_generated,
          transcript_json = excluded.transcript_json,
          transcript_text = excluded.transcript_text,
          fetched_at = excluded.fetched_at
        """,
        (
            video_id,
            transcript.language_code,
            transcript.language,
            1 if transcript.is_generated else 0,
            json.dumps(transcript.segments, ensure_ascii=False),
            transcript.text,
            fetched_at,
        ),
    )


def fetch_missing_transcripts(
    connection: sqlite3.Connection,
    *,
    languages: tuple[str, ...],
    video_id: str | None = None,
    refresh: bool = False,
    request_delay_seconds: float = DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
    max_consecutive_blocks: int = DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
) -> int:
    rows = reviewed_restaurant_rows(
        connection,
        video_id=video_id,
        missing_transcript_only=not refresh,
    )
    count = 0
    consecutive_blocks = 0
    for index, row in enumerate(rows, start=1):
        current_video_id = str(row["video_id"])
        try:
            transcript = fetch_transcript(current_video_id, languages)
        except Exception as exc:  # noqa: BLE001 - transcript availability varies by video.
            print(f"Skipped transcript {current_video_id}: {exc}")
            if is_youtube_block_error(exc):
                consecutive_blocks += 1
                if max_consecutive_blocks > 0 and consecutive_blocks >= max_consecutive_blocks:
                    print(
                        f"Stopping transcript fetch after {consecutive_blocks} consecutive YouTube block errors.",
                        flush=True,
                    )
                    break
            else:
                consecutive_blocks = 0
        else:
            upsert_transcript(connection, current_video_id, transcript, now_iso())
            connection.commit()
            count += 1
            consecutive_blocks = 0
        if request_delay_seconds > 0 and index < len(rows):
            print(f"Waiting {request_delay_seconds:g}s before the next transcript request...", flush=True)
            time.sleep(request_delay_seconds)
    return count


def load_story_review_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("reviews") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError(f"{path} must contain a reviews list")
    return [validate_story_review_item(item, path) for item in items]


def validate_story_review_item(item: Any, path: Path) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"{path} contains a non-object review item")
    required = ("video_id", "story_hook", "story_intro", "tasting_flow")
    missing = [key for key in required if not str(item.get(key, "")).strip()]
    if missing:
        video_id = item.get("video_id", "<unknown>")
        raise ValueError(f"{path} review {video_id} missing required fields: {', '.join(missing)}")
    evidence = item.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError(f"{path} review {item['video_id']} evidence must be an object")
    validate_story_review_quality(item, str(path))
    return item


def validate_story_review_quality(item: dict[str, Any], source_label: str) -> None:
    video_id = str(item.get("video_id") or "<unknown>")
    reviewer = str(item.get("reviewer") or "")
    if reviewer == DISALLOWED_STORY_REVIEWER:
        raise ValueError(f"{source_label} review {video_id} uses disallowed template reviewer")

    combined_text = " ".join(
        str(item.get(key) or "")
        for key in ("story_hook", "story_intro", "tasting_flow")
    )
    story_intro = str(item.get("story_intro") or "").strip()
    tasting_flow = str(item.get("tasting_flow") or "").strip()
    if len(story_intro) < MIN_STORY_INTRO_CHARS:
        raise ValueError(
            f"{source_label} review {video_id} story_intro is too short: "
            f"{len(story_intro)} < {MIN_STORY_INTRO_CHARS}"
        )
    if len(tasting_flow) < MIN_TASTING_FLOW_CHARS:
        raise ValueError(
            f"{source_label} review {video_id} tasting_flow is too short: "
            f"{len(tasting_flow)} < {MIN_TASTING_FLOW_CHARS}"
        )

    matched_patterns = [pattern for pattern in GENERIC_STORY_PATTERNS if pattern in combined_text]
    if matched_patterns:
        raise ValueError(
            f"{source_label} review {video_id} looks like a generic template: "
            + ", ".join(matched_patterns)
        )
    provenance_patterns = [
        pattern for pattern in PUBLIC_STORY_PROVENANCE_PATTERNS if pattern in combined_text
    ]
    if provenance_patterns:
        raise ValueError(
            f"{source_label} review {video_id} leaks source/provenance language into public story text: "
            + ", ".join(provenance_patterns)
        )

    normalized_sentences = [
        " ".join(sentence.strip().split())
        for sentence in combined_text.replace("?", ".").replace("!", ".").split(".")
        if sentence.strip()
    ]
    duplicate_sentences = sorted(
        {
            sentence
            for sentence in normalized_sentences
            if len(sentence) >= 20 and normalized_sentences.count(sentence) > 1
        }
    )
    if duplicate_sentences:
        raise ValueError(
            f"{source_label} review {video_id} repeats sentences: "
            + " / ".join(duplicate_sentences)
        )

    evidence = item.get("evidence", {})
    tasting_order = evidence.get("tasting_order") if isinstance(evidence, dict) else None
    if (
        not isinstance(tasting_order, list)
        or len([value for value in tasting_order if str(value).strip()]) < MIN_TASTING_ORDER_ITEMS
    ):
        raise ValueError(
            f"{source_label} review {video_id} must include evidence.tasting_order "
            f"with at least {MIN_TASTING_ORDER_ITEMS} items"
        )
    transcript_support = evidence.get("transcript_support") if isinstance(evidence, dict) else None
    if not isinstance(transcript_support, list):
        raise ValueError(f"{source_label} review {video_id} must include evidence.transcript_support list")
    support_items = [str(value).strip() for value in transcript_support if str(value).strip()]
    if len(support_items) < MIN_TRANSCRIPT_SUPPORT_ITEMS:
        raise ValueError(
            f"{source_label} review {video_id} must include at least "
            f"{MIN_TRANSCRIPT_SUPPORT_ITEMS} transcript support items"
        )
    weak_support_markers = ("제목에 나온다", "후보명", "회차다", "흐름이다", "구성이다")
    weak_support_items = [
        support for support in support_items
        if any(marker in support for marker in weak_support_markers)
    ]
    if len(weak_support_items) == len(support_items):
        raise ValueError(f"{source_label} review {video_id} transcript support is too generic")

    critic_rounds = item.get("critic_rounds")
    if not isinstance(critic_rounds, list) or len(critic_rounds) < MIN_STORY_CRITIC_ROUNDS:
        raise ValueError(
            f"{source_label} review {video_id} must include at least "
            f"{MIN_STORY_CRITIC_ROUNDS} critic_rounds"
        )

    for index, round_item in enumerate(critic_rounds, start=1):
        if not isinstance(round_item, dict):
            raise ValueError(f"{source_label} review {video_id} critic round {index} must be an object")
        if int(round_item.get("round") or index) != index:
            raise ValueError(f"{source_label} review {video_id} critic round {index} has wrong round number")
        decision = str(round_item.get("decision") or "")
        if decision not in {"revise", "reject", "pass"}:
            raise ValueError(f"{source_label} review {video_id} critic round {index} has invalid decision")
        writer_response = str(round_item.get("writer_response") or "").strip()
        if not writer_response:
            raise ValueError(f"{source_label} review {video_id} critic round {index} needs writer_response")
        required_changes = round_item.get("required_changes", [])
        if not isinstance(required_changes, list):
            raise ValueError(f"{source_label} review {video_id} critic round {index} required_changes must be a list")
        if index < MIN_STORY_CRITIC_ROUNDS and decision != "revise":
            raise ValueError(f"{source_label} review {video_id} critic round {index} must be revise")
        if index < MIN_STORY_CRITIC_ROUNDS and not required_changes:
            raise ValueError(f"{source_label} review {video_id} critic round {index} must require concrete changes")

    final_round = critic_rounds[-1]
    if str(final_round.get("decision") or "") != "pass":
        raise ValueError(f"{source_label} review {video_id} final critic decision must be pass")
    issues = final_round.get("issues", [])
    if issues:
        raise ValueError(f"{source_label} review {video_id} final critic issues must be empty on pass")
    checks = final_round.get("checks")
    if not isinstance(checks, dict):
        raise ValueError(f"{source_label} review {video_id} final critic checks must be an object")
    failed_checks = [name for name in REQUIRED_CRITIC_CHECKS if checks.get(name) is not True]
    if failed_checks:
        raise ValueError(f"{source_label} review {video_id} failed critic checks: {', '.join(failed_checks)}")

    revision_history = item.get("revision_history")
    if not isinstance(revision_history, list) or len(revision_history) < MIN_STORY_CRITIC_ROUNDS + 1:
        raise ValueError(
            f"{source_label} review {video_id} must include writer/critic revision_history "
            f"with at least {MIN_STORY_CRITIC_ROUNDS + 1} entries"
        )
    generic_revision_markers = (
        "검증 항목을 통과한 최종본이다",
        "긴 문장과 흐린 주어를 줄이라고 지적했다",
        "음식 순서와 주인 맥락을 넣었다",
    )
    revision_text = " ".join(
        str(entry.get("summary") or entry.get("note") or "")
        for entry in revision_history
        if isinstance(entry, dict)
    )
    if any(marker in revision_text for marker in generic_revision_markers):
        raise ValueError(f"{source_label} review {video_id} uses generic revision history")


def story_review_evidence(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    return {
        **evidence,
        "quality_policy_version": STORY_QUALITY_POLICY_VERSION,
        "critic_rounds": item.get("critic_rounds", []),
        "revision_history": item.get("revision_history", []),
    }


def apply_story_reviews(
    connection: sqlite3.Connection,
    input_path: Path,
    *,
    video_id: str | None = None,
) -> int:
    items = load_story_review_items(input_path)
    if video_id:
        items = [item for item in items if str(item["video_id"]) == video_id]

    count = 0
    for item in items:
        current_video_id = str(item["video_id"])
        exists = connection.execute(
            "select 1 from youtube_videos where video_id = ?",
            (current_video_id,),
        ).fetchone()
        if exists is None:
            raise RuntimeError(f"No YouTube video found for video_id={current_video_id}")
        connection.execute(
            """
            insert into video_story_reviews (
              external_id,
              story_intro,
              tasting_flow,
              story_hook,
              reviewer,
              evidence_json,
              generated_at
            )
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(external_id) do update set
              story_intro = excluded.story_intro,
              tasting_flow = excluded.tasting_flow,
              story_hook = excluded.story_hook,
              reviewer = excluded.reviewer,
              evidence_json = excluded.evidence_json,
              generated_at = excluded.generated_at
            """,
            (
                current_video_id,
                str(item["story_intro"]).strip(),
                str(item["tasting_flow"]).strip(),
                str(item["story_hook"]).strip(),
                str(item.get("reviewer") or "codex"),
                json.dumps(story_review_evidence(item), ensure_ascii=False),
                str(item.get("generated_at") or now_iso()),
            ),
        )
        count += 1
    return count


def missing_story_review_rows(connection: sqlite3.Connection, *, limit: int | None = None) -> list[sqlite3.Row]:
    sql = """
        select
          v.video_id,
          v.source,
          v.title,
          v.reviewed_restaurant_names,
          length(t.transcript_text) as transcript_length,
          case
            when sr.external_id is null then 'missing'
            when length(trim(sr.story_intro)) < ? then 'story_intro_too_short'
            when length(trim(sr.tasting_flow)) < ? then 'tasting_flow_too_short'
            when sr.reviewer = 'codex-story-agent' then 'legacy_story_agent_batch'
            else 'needs_refresh'
          end as story_status
        from video_pipeline_status v
        left join video_transcripts t on t.external_id = v.video_id
        left join video_story_reviews sr on sr.external_id = v.video_id
        where v.review_decision = 'restaurant_intro'
          and (
            sr.external_id is null
            or length(trim(sr.story_intro)) < ?
            or length(trim(sr.tasting_flow)) < ?
            or sr.reviewer = 'codex-story-agent'
          )
        order by v.published_at desc, v.youtube_video_id desc
    """
    params: tuple[Any, ...] = (
        MIN_STORY_INTRO_CHARS,
        MIN_TASTING_FLOW_CHARS,
        MIN_STORY_INTRO_CHARS,
        MIN_TASTING_FLOW_CHARS,
    )
    if limit is not None:
        sql += " limit ?"
        params = (*params, limit)
    return list(connection.execute(sql, params).fetchall())


def process_stories(
    sqlite_path: Path,
    *,
    input_path: Path = DEFAULT_INPUT,
    languages: tuple[str, ...] = DEFAULT_LANGUAGES,
    video_id: str | None = None,
    refresh: bool = False,
    fetch_only: bool = False,
    apply_only: bool = False,
    request_delay_seconds: float = DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
    max_consecutive_blocks: int = DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
) -> StoryProcessResult:
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        ensure_pipeline_schema(connection)
        fetched_count = 0
        if not apply_only:
            fetched_count = fetch_missing_transcripts(
                connection,
                languages=languages,
                video_id=video_id,
                refresh=refresh,
                request_delay_seconds=request_delay_seconds,
                max_consecutive_blocks=max_consecutive_blocks,
            )
        applied_count = 0
        if not fetch_only:
            applied_count = apply_story_reviews(connection, input_path, video_id=video_id)
        return StoryProcessResult(
            fetched_transcript_count=fetched_count,
            applied_review_count=applied_count,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts and apply Codex-authored story reviews."
    )
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--video-id", help="Process only one video id.")
    parser.add_argument("--refresh", action="store_true", help="Refresh already stored transcripts.")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch transcripts; do not apply story reviews.")
    parser.add_argument("--apply-only", action="store_true", help="Only apply story reviews; do not fetch transcripts.")
    parser.add_argument("--list-missing", action="store_true", help="List restaurant videos still missing Codex story reviews.")
    parser.add_argument("--limit", type=int, default=20, help="Limit for --list-missing output.")
    parser.add_argument(
        "--request-delay",
        type=float,
        default=DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS,
        help=(
            "Seconds to wait between transcript requests. "
            f"Default: {DEFAULT_TRANSCRIPT_REQUEST_DELAY_SECONDS:g}"
        ),
    )
    parser.add_argument(
        "--max-consecutive-blocks",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS,
        help=(
            "Stop transcript fetching after this many consecutive YouTube block errors. "
            f"Default: {DEFAULT_MAX_CONSECUTIVE_TRANSCRIPT_BLOCKS}"
        ),
    )
    parser.add_argument(
        "--languages",
        default="ko,en",
        help="Comma-separated transcript language preference list. Default: ko,en",
    )
    args = parser.parse_args()

    languages = tuple(item.strip() for item in args.languages.split(",") if item.strip())
    with sqlite3.connect(args.sqlite) as connection:
        connection.row_factory = sqlite3.Row
        ensure_pipeline_schema(connection)
        if args.list_missing:
            for row in missing_story_review_rows(connection, limit=args.limit):
                print(
                    f"{row['video_id']}\t{row['source']}\t{row['title']}\t"
                    f"transcript_length={row['transcript_length'] or 0}\t"
                    f"story_status={row['story_status']}"
                )
            return 0

    result = process_stories(
        args.sqlite,
        input_path=args.input,
        languages=languages or DEFAULT_LANGUAGES,
        video_id=args.video_id,
        refresh=args.refresh,
        fetch_only=args.fetch_only,
        apply_only=args.apply_only,
        request_delay_seconds=args.request_delay,
        max_consecutive_blocks=args.max_consecutive_blocks,
    )
    print(f"Fetched transcripts: {result.fetched_transcript_count}")
    print(f"Applied Codex story reviews: {result.applied_review_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
