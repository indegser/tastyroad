# tastyroad

대한민국 맛집 목록을 출처 기반으로 정리하는 Next.js 프로젝트입니다.

이 repo는 앱 코드와 데이터/config를 보관합니다. 반복 실행 로직은 repo 루트 `scripts/`가 아니라 `.codex/skills` 아래의 프로젝트 스킬과 `.codex/agents` 설정에서 관리합니다.

## 데이터

- `data/tastyroad.sqlite`: 사이트가 읽는 기준 SQLite DB
- `data/sources/youtube_sources.json`: YouTube 소스 설정
- `data/raw/youtube/*.json`: 수집 결과 mirror
- `data/agent_reviews/*.json`: 영상 검수 입력
- `data/story_reviews/*.json`: 스토리 리뷰 입력
- `data/verified_places/*.json`: 검증된 장소 승격 입력
- `data/work/`: 멀티 에이전트 작업 artifact
- `data/naver_map_list_target.json`: Naver Map 저장 리스트 설정
- `data/naver_map_list_synced_ids.json`: Naver Map 저장 완료 상태

## 스킬

- `$tastyroad-youtube-channel-collect`: YouTube 소스 수집, full-channel 감사, channel_id 확인
- `$tastyroad-data-pipeline`: SQLite 데이터 갱신, 자막/스토리/장소 pipeline, agent artifact reducer
- `$tastyroad-naver-map-sync`: 공개 식당을 Naver Map `Tastyroad` 리스트에 동기화
- `$tastyroad-site-release`: 공개 노출 계약 검증, Vercel prebuilt packaging, 배포 후 검증

## 에이전트

`.codex/agents`에는 Tastyroad 전용 에이전트 설정이 있습니다.

- `tastyroad_story_writer`
- `tastyroad_story_critic`
- `tastyroad_story_manager`
- `tastyroad_map_syncer`
- `tastyroad_map_auditor`

## 앱 빌드

```bash
pnpm run build
```

공개 노출 계약 검증과 배포 준비는 `$tastyroad-site-release` 스킬을 사용합니다.
