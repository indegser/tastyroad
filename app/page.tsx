import { DatabaseSync } from "node:sqlite";

type PlaceCandidate = {
  name: string;
  source: string;
  title: string;
  publishedAt: string;
  publishedAtLabel: string;
  publishedDateLabel: string;
  url: string;
  storyHook: string;
  storyIntro: string;
  tastingFlow: string;
};

type CandidateRow = {
  source: string;
  title: string;
  published_at: string;
  url: string;
  raw_restaurant_name_candidates: string;
  display_name: string;
  agent_restaurant_names: string;
  story_hook: string;
  story_intro: string;
  tasting_flow: string;
};

export const dynamic = "force-static";

const SQLITE_PATH = "data/tastyroad.sqlite";

function loadCandidates(limit = 500): PlaceCandidate[] {
  const db = new DatabaseSync(SQLITE_PATH, { readOnly: true });

  try {
    const rows = db
      .prepare(
        `
        with reviewed as (
          select
            external_id,
            decision,
            confidence,
            restaurant_names,
            case
              when detected_restaurant_count > 0 then detected_restaurant_count
              when json_valid(restaurant_names) then json_array_length(restaurant_names)
              else 0
            end as detected_restaurant_count
          from agent_video_reviews
        ),
        mapped as (
          select
            mention_candidate_id,
            count(distinct restaurant_id) as mapped_restaurant_count
          from mentions
          group by mention_candidate_id
        ),
        picked_mention as (
          select mention_candidate_id, min(id) as id
          from mentions
          group by mention_candidate_id
        )
        select
          s.name as source,
          c.title,
          c.published_at,
          c.url,
          c.raw_restaurant_name_candidates,
          coalesce(restaurants.display_name, '') as display_name,
          coalesce(reviewed.restaurant_names, '[]') as agent_restaurant_names,
          coalesce(story.story_hook, '') as story_hook,
          coalesce(story.story_intro, '') as story_intro,
          coalesce(story.tasting_flow, '') as tasting_flow
        from mention_candidates c
        join sources s on s.id = c.source_id
        join reviewed on reviewed.external_id = c.external_id
        join mapped on mapped.mention_candidate_id = c.id
        left join picked_mention on picked_mention.mention_candidate_id = c.id
        left join mentions on mentions.id = picked_mention.id
        left join restaurants on restaurants.id = mentions.restaurant_id
        join video_story_reviews story on story.external_id = c.external_id
        where reviewed.decision = 'restaurant_intro'
          and mapped.mapped_restaurant_count >= max(coalesce(reviewed.detected_restaurant_count, 1), 1)
          and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
        order by c.published_at desc, c.id desc
        limit ?
        `,
      )
      .all(limit) as CandidateRow[];

    return rows.map((row) => ({
      name:
        row.display_name ||
        firstNameCandidate(row.agent_restaurant_names) ||
        firstNameCandidate(row.raw_restaurant_name_candidates),
      source: row.source,
      title: row.title,
      publishedAt: row.published_at,
      publishedAtLabel: formatDateTime(row.published_at),
      publishedDateLabel: formatDate(row.published_at),
      url: row.url,
      storyHook: row.story_hook.trim(),
      storyIntro: row.story_intro.trim(),
      tastingFlow: row.tasting_flow.trim(),
    }));
  } finally {
    db.close();
  }
}

function firstNameCandidate(rawValue: string) {
  try {
    const values = JSON.parse(rawValue) as unknown;
    return Array.isArray(values) && values.length > 0 ? String(values[0]) : "";
  } catch {
    return "";
  }
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "알 수 없음";
  }

  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(value));
}

function formatDate(value: string | null) {
  if (!value) {
    return "알 수 없음";
  }

  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

export default function Home() {
  const items = loadCandidates();
  const latestPublishedAt = items[0]?.publishedAtLabel ?? "알 수 없음";

  return (
    <main>
      <header>
        <p className="muted">최신 영상: {latestPublishedAt}</p>
        <h1>맛집 최신 크롤링</h1>
        <p className="summary muted">
          스토리와 지도 매핑이 모두 완료된 맛집 영상만 발행일 최신순으로 정리했습니다.
        </p>
      </header>

      <ol className="video-list">
        {items.map((candidate, index) => (
          <li key={`${candidate.url}-${index}`}>
            <article className="video-card">
              <div className="video-info">
                <h2>{candidate.name}</h2>
                <p className="source-line">
                  <span>{candidate.source}</span>
                  {candidate.storyHook ? (
                    <>
                      <span className="separator" aria-hidden="true">
                        -
                      </span>
                      <span className="source-hook">{candidate.storyHook}</span>
                    </>
                  ) : null}
                </p>
                <a className="video-link" href={candidate.url}>
                  <span>{candidate.title}</span>
                  <span className="separator" aria-hidden="true">
                    -
                  </span>
                  <span className="video-date">{candidate.publishedDateLabel}</span>
                  <span aria-hidden="true">↗</span>
                </a>
                {candidate.storyIntro ? (
                  <section className="story-section" aria-label="이야기">
                    <h3>이야기</h3>
                    <p>{candidate.storyIntro}</p>
                  </section>
                ) : null}
                {candidate.tastingFlow ? (
                  <section className="tasting-flow" aria-label="시식 메뉴 및 순서">
                    <h3>시식 메뉴 및 순서</h3>
                    <p>{candidate.tastingFlow}</p>
                  </section>
                ) : null}
              </div>
            </article>
          </li>
        ))}
      </ol>
    </main>
  );
}
