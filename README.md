# tastyroad

대한민국 맛집 목록을 출처 기반으로 재정의하기 위한 데이터 수집 프로젝트입니다.

YouTube API 없이 공개 RSS 피드를 사용해 새 영상을 감지하고, 채널별 설정에 맞는 영상만 후보 데이터로 저장합니다.

## YouTube 소스 수집

```bash
python3 scripts/collect_youtube.py
```

기본 출력:

```txt
data/raw/youtube/{source_key}.json
data/tastyroad.sqlite
```

소스 설정:

```txt
data/sources/youtube_sources.json
```

소스 하나는 아래 필드로 정의합니다.

```json
{
  "key": "sungsikyung_mukeultende",
  "name": "성시경의 먹을텐데",
  "type": "youtube",
  "trust_tier": "A",
  "channel_id": "UCl23-Cci_SMqyGXE1T_LYUg",
  "official_url": "https://www.youtube.com/channel/UCl23-Cci_SMqyGXE1T_LYUg",
  "enabled": true,
  "title_include_any": ["먹을텐데"],
  "title_exclude_any": [],
  "title_cleanup_patterns": [
    "^\\[?sub\\]?\\s*",
    "^성시경의\\s*먹을텐데\\s*[|lㅣ]?\\s*",
    "\\s*\\([^)]*\\)\\s*$"
  ]
}
```

특정 소스만 수집:

```bash
python3 scripts/collect_youtube.py --source sungsikyung_mukeultende
```

채널 URL에서 `channel_id` 확인:

```bash
python3 scripts/resolve_youtube_channel_id.py "https://www.youtube.com/@somehandle"
```

기존 성시경 전용 명령도 wrapper로 유지합니다.

```bash
python3 scripts/collect_sungsikyung.py
```

수집하는 필드:

- `source_key`: 내부 소스 키
- `source`: 출처명
- `channel_id`: YouTube 채널 ID
- `video_id`
- `title`
- `url`
- `thumbnail_url`: YouTube 영상 썸네일 URL
- `published_at`
- `updated_at`
- `description`: 영상 설명란
- `duration_seconds`: 영상 길이(초)
- `tags`: YouTube 태그
- `chapters`: 영상 챕터
- `restaurant_name_candidates`: 제목에서 추정한 식당명/지역 후보
- `collected_at`

이 단계의 데이터는 최종 식당 DB가 아니라 `MentionCandidate`입니다. 수집된 영상은 검수 여부와 관계없이 모두 DB에 남고, 이후 단계에서 상태만 추가됩니다.

## 파이프라인 상태 모델

영상 수집 파이프라인은 `수집 > 검수 > 지도 매핑` 3단계입니다. 웹사이트 빌드/배포는 이 DB를 읽는 별도 소비자이며, 파이프라인 상태를 만들거나 바꾸는 책임을 갖지 않습니다.

1. `수집`: YouTube RSS/yt-dlp 결과를 `mention_candidates`에 저장합니다. 이 단계의 영상은 아직 맛집 영상인지 모릅니다.
2. `검수`: `agent_video_reviews`에 영상 단위 판정을 저장합니다. `decision`은 `restaurant_intro`, `not_restaurant`, `uncertain` 중 하나이고, `detected_restaurant_count`로 영상 안 식당 수를 명시합니다. 식당명이 추정되면 `restaurant_names`에도 남깁니다.
3. `지도 매핑`: Google/Naver/Kakao 지도 검색 결과 또는 보조 웹 증거를 `place_resolution_candidates`에 남기고, 확정된 지도 entity는 `restaurants`, `place_links`, `mentions`로 승격합니다. 가능하면 `map_provider`는 `google_maps`, `naver_map`, `kakao_map` 중 하나를 우선 사용합니다.

현재 상태는 DB 뷰로 바로 확인합니다.

```bash
python3 scripts/pipeline_status.py
```

핵심 쿼리:

```sql
select review_status, mapping_status, count(*)
from video_pipeline_status
group by review_status, mapping_status;
```

```sql
select video_id, source, title
from unreviewed_videos
order by published_at desc;
```

```sql
select video_id, title, detected_restaurant_count, mapped_restaurant_count
from mapping_backlog
order by published_at desc;
```

수집된 영상은 모두 영상 단위 검수 대상입니다. 검수 결과가 없거나 `restaurant_intro`로 통과하지 않은 영상은 리스팅 데이터에 포함되지 않습니다. 미검수 백로그는 빌드와 독립적으로 확인합니다.

```bash
python3 scripts/apply_agent_reviews.py
python3 scripts/apply_agent_reviews.py --check-coverage
```

검수 누락 영상 확인:

```bash
python3 scripts/apply_agent_reviews.py --list-unreviewed
```

SQLite 확인:

```bash
sqlite3 data/tastyroad.sqlite "select s.name, m.title, m.published_at, m.url from mention_candidates m join sources s on s.id = m.source_id order by m.published_at desc;"
```

## 장소 정규화

지도/장소 서비스 검색으로 식당 엔티티까지 승격할 수 있도록 검증 seed를 분리했습니다.

```bash
python3 scripts/promote_verified_places.py
```

입력:

```txt
data/verified_places/sungsikyung_mukeultende_places.json
```

검증 seed 전체를 한 번에 승격:

```bash
python3 scripts/promote_verified_places.py --input-dir data/verified_places
```

추가 생성/갱신 테이블:

- `restaurants`: 정규화된 식당
- `place_links`: 지도 서비스 링크, 증거 URL, confidence
- `mentions`: 특정 영상 후보와 식당의 연결
- `place_resolution_candidates`: 지도 검색 후보, 선택된 결과, 검색 provider, 검색어, 증거 JSON

확인:

```bash
sqlite3 data/tastyroad.sqlite "select r.display_name, r.address, p.provider, m.confidence, m.status from restaurants r join mentions m on m.restaurant_id = r.id join place_links p on p.restaurant_id = r.id order by m.confidence desc;"
```

## E2E 실행

```bash
python3 scripts/run_e2e.py
```

이 명령은 RSS 수집, SQLite 적재, 검증된 장소 승격, 조인 검증을 한 번에 수행합니다.

## 자동 업데이트, PR, 배포

`taste.indegser.com`은 `index.html` 정적 페이지를 Vercel `tastyroad` 프로젝트에 배포합니다.

수집 데이터와 검증 seed로 정적 페이지를 다시 생성:

```bash
python3 scripts/build_site.py
```

`build_site.py`는 RSS 수집, 영상 검수 적용, 검증 seed 승격, 정적 페이지 렌더링, 썸네일/업로드일 UI 검증을 순서대로 실행하고 `public/index.html`을 생성합니다. 미검수 영상이 남아 있어도 빌드는 실패하지 않고, 검수 통과 영상만 리스팅합니다.

수집, 검증 seed 승격, 정적 페이지 렌더링을 순서대로 실행하고 페이지 출력이 바뀐 경우에만 Vercel production으로 재배포:

```bash
python3 scripts/deploy_if_changed.py
```

동일한 명령을 npm script로도 실행할 수 있습니다.

```bash
pnpm run deploy:changed
```

GitHub Actions는 두 단계로 동작합니다.

- `Update Tastyroad Data`: 매시간 RSS/YouTube 데이터를 수집하고 `public/index.html`을 빌드합니다. 변경이 있으면 `tastyroad/auto-update` 브랜치로 PR을 만들고 자동으로 squash merge합니다.
- `Deploy Tastyroad`: `main`에 push가 생기면 HTML을 다시 빌드하고 Vercel production으로 배포합니다.

자동 PR/머지는 GitHub App 토큰을 우선 사용합니다. repository secrets에 아래 값을 넣습니다.

```txt
TASTYROAD_APP_ID
TASTYROAD_APP_PRIVATE_KEY
```

GitHub App에는 이 repository에 대해 최소한 아래 권한이 필요합니다.

- Contents: Read and write
- Pull requests: Read and write

GitHub App secret이 없으면 workflow는 `GITHUB_TOKEN`으로 fallback합니다. 다만 `GITHUB_TOKEN`은 GitHub Actions 재트리거 정책에 걸릴 수 있으므로, 배포까지 완전 자동으로 이어가려면 GitHub App secret을 넣는 구성이 안전합니다.
fallback 경로에서도 자동 배포가 끊기지 않도록 `Update Tastyroad Data` workflow는 PR merge 직후 Vercel production 배포를 직접 실행합니다.

Vercel 배포용 repository secrets도 필요합니다.

```txt
VERCEL_TOKEN
VERCEL_ORG_ID=team_jyYah1TfVqWBxPRhZRQnTlN7
VERCEL_PROJECT_ID=prj_xP4QInXXAVeQTPbvBJPKYiijR0SC
```
