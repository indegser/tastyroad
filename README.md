# tastyroad

대한민국 맛집 목록을 출처 기반으로 정리하는 Next.js 프로젝트입니다.

이 repo는 앱 코드와 데이터/config를 보관합니다. 반복 실행 로직은 repo 루트 `scripts/`가 아니라 `.codex/skills` 아래의 프로젝트 스킬과 `.codex/agents` 설정에서 관리합니다.

## 데이터

- `data/tastyroad.sqlite`: 사이트가 읽는 기준 SQLite DB 및 파이프라인 메타데이터 DB
- Supabase Storage `tastyroad-transcripts`: YouTube 자막 raw track/segment 원천 아카이브
- `data/sources/youtube_sources.json`: YouTube 소스 설정
- `data/raw/youtube/*.json`: 수집 결과 mirror
- `data/agent_reviews/*.json`: 영상 검수 입력
- `data/tastyroad.sqlite`의 `youtube_transcript_*` 테이블: YouTube 자막 fetch 이력, preferred track, object storage path metadata, legacy segment cache
- `data/tastyroad.sqlite`의 `video_must_taste_items` 테이블: 식당별 자막 근거 필수 맛보기 추천 저장소
- `data/verified_places/*.json`: 검증된 장소 승격 입력
- `data/work/`: 멀티 에이전트 작업 artifact
- `data/work/must_taste/`: 자막 기반 필수 맛보기 추천 추출 작업 artifact
- `data/work/map_video_restaurants/`: 식당 매핑 후보/장소 검토 작업 artifact
- `data/naver_map_list_target.json`: Naver Map 저장 리스트 설정
- `data/naver_map_list_synced_ids.json`: Naver Map 저장 완료 상태

## 스킬

- `$tastyroad-regular-source-automation`: Codex app Automation에서 실행하는 정기 전체 소스 점검 오케스트레이션. 신규 영상 수집, 자막 수집, 결정적 지도 후보 처리, must-taste 큐/게이트 리포트, 배포 가능 여부 판단을 수행하고, 자막/must-taste 미완료는 배포 차단이 아닌 Triage warnings로 남김
- `$tastyroad-youtube-channel-collect`: YouTube 소스 수집/갱신, full-channel 감사, channel_id 확인
- `$tastyroad-youtube-transcript-ingest`: Webshare 기반 YouTube 자막 다운로드, Supabase Storage raw/segment 아카이브, SQLite metadata 저장
- `$tastyroad-transcript-must-taste`: object-storage-backed 또는 SQLite cached 자막 segment 전체 스캔, attention 후보 집계, 후보 리뷰, 탈락 사유까지 거쳐 식당별 꼭 맛볼 추천 메뉴 최대 3개와 직접 자막 인용 추출/검증/저장
- `$tastyroad-map-video-restaurants`: `mapping_pending`/`needs_review` 조회, 애매한 매핑의 에이전트 후보/장소 검토, Naver place ID 검증, `restaurants`/`youtube_video_restaurants` 반영
- `$tastyroad-naver-map-sync`: 공개 식당을 Naver Map `Tastyroad` 리스트에 동기화
- `$tastyroad-site-release`: GitHub push 기반 Vercel 배포, 배포 상태/응답 확인, 배포 후 API 검증

## 정기 자동화

정기적인 신규 영상 점검은 GitHub Actions가 아니라 Codex app Automation을 기본 실행기로 사용합니다. Automation은 Tastyroad 프로젝트에 연결된 dedicated worktree에서 `$tastyroad-regular-source-automation`을 호출합니다.

권장 Automation prompt는 `.codex/skills/tastyroad-regular-source-automation/scripts/automation_prompt.md`에 있습니다. 배포는 지도 매핑과 빌드 같은 hard publishing gate가 통과한 뒤 `$tastyroad-site-release`로 진행합니다. 자막 수집 실패나 must-taste 미완료는 식당 공개 노출을 막지 않고 후속 Triage warning으로 남깁니다.

## 에이전트

`.codex/agents`에는 Tastyroad 전용 에이전트 설정이 있습니다.

- `tastyroad_map_syncer`
- `tastyroad_map_auditor`

## 앱 빌드

```bash
pnpm run build
```

GitHub 연동 Vercel 배포와 배포 후 응답 확인은 `$tastyroad-site-release` 스킬을 사용합니다.
