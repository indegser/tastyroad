import { DatabaseSync } from "node:sqlite";
import path from "node:path";
import { normalizeRegion } from "./region";
import type {
  FacetValue,
  MustTasteItem,
  RestaurantFacets,
  RestaurantItem,
  RestaurantSearchParams,
  RestaurantSearchResponse,
} from "./types";

const SQLITE_PATH = path.join(process.cwd(), "data/tastyroad.sqlite");
const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;
const NAME_INITIAL_FACETS = [
  "ㄱ",
  "ㄴ",
  "ㄷ",
  "ㄹ",
  "ㅁ",
  "ㅂ",
  "ㅅ",
  "ㅇ",
  "ㅈ",
  "ㅊ",
  "ㅋ",
  "ㅌ",
  "ㅍ",
  "ㅎ",
  "#",
];
const HANGUL_INITIALS = [
  "ㄱ",
  "ㄲ",
  "ㄴ",
  "ㄷ",
  "ㄸ",
  "ㄹ",
  "ㅁ",
  "ㅂ",
  "ㅃ",
  "ㅅ",
  "ㅆ",
  "ㅇ",
  "ㅈ",
  "ㅉ",
  "ㅊ",
  "ㅋ",
  "ㅌ",
  "ㅍ",
  "ㅎ",
];
const HANGUL_INITIAL_GROUPS: Record<string, string> = {
  "ㄲ": "ㄱ",
  "ㄸ": "ㄷ",
  "ㅃ": "ㅂ",
  "ㅆ": "ㅅ",
  "ㅉ": "ㅈ",
};
const HANGUL_SYLLABLE_START = 0xac00;
const HANGUL_SYLLABLE_END = 0xd7a3;
const HANGUL_SYLLABLES_PER_INITIAL = 588;

type RestaurantRow = {
  id: number;
  name: string;
  country_code: string;
  raw_region: string | null;
  address: string;
  category: string | null;
  status: string;
  naver_map_id: string;
  source: string | null;
  source_title: string | null;
  source_url: string | null;
  source_thumbnail_url: string | null;
  source_published_at: string | null;
  map_url: string | null;
  must_taste_json: string | null;
};

export function normalizeRestaurantSearchParams(
  params: URLSearchParams,
): RestaurantSearchParams {
  return {
    q: normalizeText(params.get("q")),
    sources: normalizeSourceParams(params),
    region: normalizeText(params.get("region")),
    regionCluster: normalizeText(params.get("regionCluster")),
    nameInitial: normalizeNameInitial(params.get("nameInitial")),
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
    facets: params.includeFacets ? buildFacets(allItems, params) : undefined,
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
            r.naver_map_id,
            s.name as source,
            c.title as source_title,
            c.url as source_url,
            c.thumbnail_url as source_thumbnail_url,
            c.published_at as source_published_at,
            c.id as source_video_row_id,
            top3.must_taste_json,
            row_number() over (
              partition by r.id
              order by c.published_at desc, c.id desc
            ) as mention_rank
          from restaurants r
          join youtube_video_restaurants m on m.restaurant_id = r.id
          join youtube_videos c on c.id = m.youtube_video_id
          join sources s on s.id = c.source_id
          left join (
            select
              restaurant_id,
              youtube_video_id,
              json_group_array(
                json_object(
                  'rank', rank,
                  'menuItem', item_name,
                  'reason', reason,
                  'timestamp', timestamp_label,
                  'evidence', evidence_text
                )
              ) as must_taste_json
            from (
              select
                restaurant_id,
                youtube_video_id,
                rank,
                item_name,
                reason,
                timestamp_label,
                evidence_text
              from video_must_taste_items
              order by restaurant_id, youtube_video_id, rank
            )
            group by restaurant_id, youtube_video_id
          ) top3 on top3.restaurant_id = r.id
            and top3.youtube_video_id = c.id
          where trim(r.naver_map_id) != ''
            and m.status in ('verified', 'metadata_verified')
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
            and url not like '%/p/search/%'
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
          ranked_mentions.source_thumbnail_url,
          ranked_mentions.source_published_at,
          coalesce(
            ranked_links.url,
            'https://map.naver.com/p/entry/place/' || ranked_mentions.naver_map_id
          ) as map_url,
          ranked_mentions.must_taste_json
        from ranked_mentions
        left join ranked_links on ranked_links.restaurant_id = ranked_mentions.id
          and ranked_links.link_rank = 1
        where ranked_mentions.mention_rank = 1
        order by
          ranked_mentions.source_published_at desc,
          ranked_mentions.source_video_row_id desc,
          ranked_mentions.id asc
        `,
      )
      .all() as RestaurantRow[];

    return rows.map((row) => ({
      id: row.id,
      name: row.name,
      address: row.address,
      category: row.category || "",
      status: row.status,
      source: row.source || "",
      sourceTitle: row.source_title || "",
      sourceUrl: row.source_url || "",
      sourceThumbnailUrl: row.source_thumbnail_url || "",
      sourcePublishedAt: row.source_published_at || "",
      mapUrl: row.map_url || "",
      mustTasteItems: parseMustTasteItems(row.must_taste_json),
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
    if (params.sources.length > 0 && !params.sources.includes(item.source)) {
      return false;
    }
    if (params.region && item.region.region !== params.region) {
      return false;
    }
    if (params.regionCluster && item.region.cluster !== params.regionCluster) {
      return false;
    }
    if (params.nameInitial && getRestaurantNameInitial(item.name) !== params.nameInitial) {
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
      ...item.mustTasteItems.flatMap((mustTasteItem) => [
        mustTasteItem.menuItem,
        mustTasteItem.reason,
        mustTasteItem.timestamp,
        mustTasteItem.evidence,
      ]),
      item.region.region,
      item.region.cluster,
    ]
      .join(" ")
      .toLocaleLowerCase("ko-KR")
      .includes(query);
  });
}

function buildFacets(
  items: RestaurantItem[],
  params: RestaurantSearchParams,
): RestaurantFacets {
  return {
    nameInitials: sortNameInitialFacets(
      countFacet(
        filterRestaurants(items, { ...params, nameInitial: "" }).map((item) =>
          getRestaurantNameInitial(item.name),
        ),
      ),
    ),
    sources: countFacet(
      filterRestaurants(items, { ...params, sources: [] }).map((item) => item.source),
    ),
    regionClusters: countFacet(
      filterRestaurants(items, {
        ...params,
        region: "",
        regionCluster: "",
      }).map((item) => item.region.cluster),
    ),
    regions: countFacet(
      filterRestaurants(items, { ...params, region: "" }).map(
        (item) => item.region.region,
      ),
    ),
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

function sortNameInitialFacets(values: FacetValue[]) {
  const order = new Map(NAME_INITIAL_FACETS.map((value, index) => [value, index]));

  return values.sort(
    (a, b) =>
      (order.get(a.value) ?? Number.MAX_SAFE_INTEGER) -
        (order.get(b.value) ?? Number.MAX_SAFE_INTEGER) ||
      a.value.localeCompare(b.value, "ko-KR"),
  );
}

function normalizeText(value: string | null) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function parseMustTasteItems(value: string | null): MustTasteItem[] {
  if (!value) {
    return [];
  }

  try {
    const parsed = JSON.parse(value) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }
        const entry = item as Record<string, unknown>;
        return {
          rank: normalizePositiveInteger(String(entry.rank || ""), 0),
          menuItem: normalizeText(String(entry.menuItem || "")),
          reason: normalizeText(String(entry.reason || "")),
          timestamp: normalizeText(String(entry.timestamp || "")),
          evidence: normalizeText(String(entry.evidence || "")),
        };
      })
      .filter((item): item is MustTasteItem => {
        return Boolean(
          item &&
            item.rank >= 1 &&
            item.rank <= 3 &&
            item.menuItem &&
            item.reason &&
            item.timestamp,
        );
      })
      .sort((a, b) => a.rank - b.rank);
  } catch {
    return [];
  }
}

function normalizeSourceParams(params: URLSearchParams) {
  const values = params.getAll("source").flatMap((value) => value.split(","));
  const deduped = new Set<string>();

  for (const value of values) {
    const normalized = normalizeText(value);
    if (normalized) {
      deduped.add(normalized);
    }
  }

  return Array.from(deduped);
}

function normalizeNameInitial(value: string | null) {
  const normalized = normalizeText(value);

  return NAME_INITIAL_FACETS.includes(normalized) ? normalized : "";
}

function getRestaurantNameInitial(name: string) {
  const firstCharacter = normalizeText(name).charAt(0);
  const codePoint = firstCharacter.charCodeAt(0);

  if (codePoint >= HANGUL_SYLLABLE_START && codePoint <= HANGUL_SYLLABLE_END) {
    const initialIndex = Math.floor(
      (codePoint - HANGUL_SYLLABLE_START) / HANGUL_SYLLABLES_PER_INITIAL,
    );
    const initial = HANGUL_INITIALS[initialIndex] || "#";
    return HANGUL_INITIAL_GROUPS[initial] || initial;
  }

  if (NAME_INITIAL_FACETS.includes(firstCharacter)) {
    return firstCharacter;
  }

  return "#";
}

function normalizePositiveInteger(value: string | null, fallback: number) {
  if (!value) {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
