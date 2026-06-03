import { DatabaseSync } from "node:sqlite";
import path from "node:path";
import { normalizeRegion } from "./region";
import type {
  FacetValue,
  RestaurantFacets,
  RestaurantItem,
  RestaurantSearchParams,
  RestaurantSearchResponse,
} from "./types";

const SQLITE_PATH = path.join(process.cwd(), "data/tastyroad.sqlite");
const MIN_STORY_INTRO_CHARS = 240;
const MIN_TASTING_FLOW_CHARS = 180;
const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;

type RestaurantRow = {
  id: number;
  name: string;
  country_code: string;
  raw_region: string | null;
  address: string;
  category: string | null;
  status: string;
  source: string | null;
  source_title: string | null;
  source_url: string | null;
  map_url: string | null;
  story_hook: string | null;
  story_intro: string | null;
  tasting_flow: string | null;
};

export function normalizeRestaurantSearchParams(
  params: URLSearchParams,
): RestaurantSearchParams {
  return {
    q: normalizeText(params.get("q")),
    source: normalizeText(params.get("source")),
    region: normalizeText(params.get("region")),
    regionCluster: normalizeText(params.get("regionCluster")),
    page: normalizePositiveInteger(params.get("page"), DEFAULT_PAGE),
    limit: Math.min(normalizePositiveInteger(params.get("limit"), DEFAULT_LIMIT), MAX_LIMIT),
    includeFacets: params.get("includeFacets") === "true",
  };
}

export function searchRestaurants(
  params: RestaurantSearchParams,
): RestaurantSearchResponse {
  const allItems = loadRestaurantItems();
  const filteredItems = filterRestaurants(allItems, params);
  const total = filteredItems.length;
  const totalPages = total > 0 ? Math.ceil(total / params.limit) : 0;
  const page = Math.min(params.page, Math.max(totalPages, 1));
  const offset = (page - 1) * params.limit;
  const items = filteredItems.slice(offset, offset + params.limit);

  return {
    items,
    page,
    limit: params.limit,
    total,
    totalPages,
    facets: params.includeFacets ? buildFacets(filteredItems) : undefined,
  };
}

function loadRestaurantItems(): RestaurantItem[] {
  const db = new DatabaseSync(SQLITE_PATH, { readOnly: true });

  try {
    const rows = db
      .prepare(
        `
        with ranked_mentions as (
          select
            r.id,
            r.display_name as name,
            r.country_code,
            r.region as raw_region,
            r.address,
            r.category,
            r.status,
            s.name as source,
            c.title as source_title,
            c.url as source_url,
            story.story_hook,
            story.story_intro,
            story.tasting_flow,
            row_number() over (
              partition by r.id
              order by c.published_at desc, c.id desc
            ) as mention_rank
          from restaurants r
          join mentions m on m.restaurant_id = r.id
          join mention_candidates c on c.id = m.mention_candidate_id
          join sources s on s.id = c.source_id
          join agent_video_reviews review on review.external_id = c.external_id
          join video_story_reviews story on story.external_id = c.external_id
          where review.decision = 'restaurant_intro'
            and (trim(story.story_hook) != '' or trim(story.story_intro) != '')
            and length(trim(story.story_intro)) >= ?
            and length(trim(story.tasting_flow)) >= ?
        ),
        ranked_links as (
          select
            restaurant_id,
            url,
            row_number() over (
              partition by restaurant_id
              order by
                case provider when 'naver_map' then 0 when 'google_maps' then 1 else 2 end,
                confidence desc,
                verified_at desc
            ) as link_rank
          from place_links
          where status in ('verified', 'metadata_verified')
        )
        select
          ranked_mentions.id,
          ranked_mentions.name,
          ranked_mentions.country_code,
          ranked_mentions.raw_region,
          ranked_mentions.address,
          ranked_mentions.category,
          ranked_mentions.status,
          ranked_mentions.source,
          ranked_mentions.source_title,
          ranked_mentions.source_url,
          ranked_links.url as map_url,
          ranked_mentions.story_hook,
          ranked_mentions.story_intro,
          ranked_mentions.tasting_flow
        from ranked_mentions
        left join ranked_links on ranked_links.restaurant_id = ranked_mentions.id
          and ranked_links.link_rank = 1
        where ranked_mentions.mention_rank = 1
        order by ranked_mentions.name asc, ranked_mentions.id asc
        `,
      )
      .all(MIN_STORY_INTRO_CHARS, MIN_TASTING_FLOW_CHARS) as RestaurantRow[];

    return rows.map((row) => ({
      id: row.id,
      name: row.name,
      address: row.address,
      category: row.category || "",
      status: row.status,
      source: row.source || "",
      sourceTitle: row.source_title || "",
      sourceUrl: row.source_url || "",
      mapUrl: row.map_url || "",
      storyHook: row.story_hook?.trim() || "",
      storyIntro: row.story_intro?.trim() || "",
      tastingFlow: row.tasting_flow?.trim() || "",
      region: normalizeRegion({
        region: row.raw_region,
        address: row.address,
        countryCode: row.country_code,
      }),
    }));
  } finally {
    db.close();
  }
}

function filterRestaurants(
  items: RestaurantItem[],
  params: RestaurantSearchParams,
) {
  const query = params.q.toLocaleLowerCase("ko-KR");

  return items.filter((item) => {
    if (params.source && item.source !== params.source) {
      return false;
    }
    if (params.region && item.region.region !== params.region) {
      return false;
    }
    if (params.regionCluster && item.region.cluster !== params.regionCluster) {
      return false;
    }
    if (!query) {
      return true;
    }

    return [
      item.name,
      item.address,
      item.category,
      item.source,
      item.sourceTitle,
      item.storyHook,
      item.storyIntro,
      item.tastingFlow,
      item.region.region,
      item.region.cluster,
    ]
      .join(" ")
      .toLocaleLowerCase("ko-KR")
      .includes(query);
  });
}

function buildFacets(items: RestaurantItem[]): RestaurantFacets {
  return {
    sources: countFacet(items.map((item) => item.source)),
    regionClusters: countFacet(items.map((item) => item.region.cluster)),
    regions: countFacet(items.map((item) => item.region.region)),
  };
}

function countFacet(values: string[]): FacetValue[] {
  const counts = new Map<string, number>();

  for (const value of values) {
    const key = value.trim();
    if (!key) {
      continue;
    }
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value, "ko-KR"));
}

function normalizeText(value: string | null) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function normalizePositiveInteger(value: string | null, fallback: number) {
  if (!value) {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
