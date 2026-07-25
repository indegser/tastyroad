import { DatabaseSync, type StatementSync } from "node:sqlite";
import path from "node:path";
import type {
  FacetValue,
  MustTasteItem,
  RestaurantFacets,
  RestaurantItem,
  RestaurantSearchParams,
  RestaurantSearchResponse,
} from "./types";

const SQLITE_PATH = path.join(process.cwd(), "data/tastyroad-public.sqlite");
const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;
const MAX_SEARCH_CACHE_ENTRIES = 100;
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

let database: DatabaseSync | undefined;
const statements = new Map<string, StatementSync>();
const searchIdsCache = new Map<string, string>();

type PublicRestaurantRow = {
  id: number;
  name: string;
  address: string;
  category: string;
  status: string;
  source: string;
  source_title: string;
  source_url: string;
  source_thumbnail_url: string;
  source_published_at: string;
  map_url: string;
  must_taste_json: string;
  country: string;
  province: string;
  city: string;
  district: string;
  region: string;
  region_cluster: string;
};

type FacetRow = {
  value: string;
  count: number;
};

type FilterDimension = "source" | "region" | "regionCluster" | "nameInitial";
type FacetColumn = "name_initial" | "source" | "region_cluster" | "region";
type SqlValue = string | number;

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
  const database = getDatabase();
  const searchIdsJson = loadSearchIdsJson(database, params.q);
  const filters = buildWhere(params, new Set(), searchIdsJson);
  const totalRow = prepare(
    database,
    `select count(*) as total from public_restaurants ${filters.sql}`,
  )
    .get(...filters.values) as { total: number };
  const total = totalRow.total;
  const totalPages = total > 0 ? Math.ceil(total / params.limit) : 0;
  const page = Math.min(params.page, Math.max(totalPages, 1));
  const offset = (page - 1) * params.limit;

  const rows = prepare(
    database,
    `
      select
        id,
        name,
        address,
        category,
        status,
        source,
        source_title,
        source_url,
        source_thumbnail_url,
        source_published_at,
        map_url,
        must_taste_json,
        country,
        province,
        city,
        district,
        region,
        region_cluster
      from public_restaurants
      ${filters.sql}
      order by sort_rank
      limit ? offset ?
    `,
  )
    .all(...filters.values, params.limit, offset) as PublicRestaurantRow[];

  return {
    items: rows.map(toRestaurantItem),
    page,
    limit: params.limit,
    total,
    totalPages,
    facets: params.includeFacets
      ? loadFacets(database, params, searchIdsJson)
      : undefined,
  };
}

function getDatabase() {
  if (!database) {
    database = new DatabaseSync(SQLITE_PATH, { readOnly: true });
    database.exec(`
      pragma query_only = on;
      pragma cache_size = -8192;
      pragma mmap_size = 8388608;
    `);
  }
  return database;
}

function prepare(database: DatabaseSync, sql: string) {
  const cached = statements.get(sql);
  if (cached) {
    return cached;
  }

  const statement = database.prepare(sql);
  statements.set(sql, statement);
  return statement;
}

function buildWhere(
  params: RestaurantSearchParams,
  excluded: ReadonlySet<FilterDimension>,
  searchIdsJson: string | undefined,
) {
  const clauses: string[] = [];
  const values: SqlValue[] = [];

  if (searchIdsJson !== undefined) {
    clauses.push("id in (select value from json_each(?))");
    values.push(searchIdsJson);
  }
  if (params.sources.length > 0 && !excluded.has("source")) {
    clauses.push(`source in (${params.sources.map(() => "?").join(", ")})`);
    values.push(...params.sources);
  }
  if (params.region && !excluded.has("region")) {
    clauses.push("region = ?");
    values.push(params.region);
  }
  if (params.regionCluster && !excluded.has("regionCluster")) {
    clauses.push("region_cluster = ?");
    values.push(params.regionCluster);
  }
  if (params.nameInitial && !excluded.has("nameInitial")) {
    clauses.push("name_initial = ?");
    values.push(params.nameInitial);
  }

  return {
    sql: clauses.length > 0 ? `where ${clauses.join(" and ")}` : "",
    values,
  };
}

function loadFacets(
  database: DatabaseSync,
  params: RestaurantSearchParams,
  searchIdsJson: string | undefined,
): RestaurantFacets {
  return {
    nameInitials: sortNameInitialFacets(
      loadFacet(
        database,
        params,
        "name_initial",
        new Set(["nameInitial"]),
        searchIdsJson,
      ),
    ),
    sources: loadFacet(
      database,
      params,
      "source",
      new Set(["source"]),
      searchIdsJson,
    ),
    regionClusters: loadFacet(
      database,
      params,
      "region_cluster",
      new Set(["region", "regionCluster"]),
      searchIdsJson,
    ),
    regions: loadFacet(
      database,
      params,
      "region",
      new Set(["region"]),
      searchIdsJson,
    ),
  };
}

function loadFacet(
  database: DatabaseSync,
  params: RestaurantSearchParams,
  column: FacetColumn,
  excluded: ReadonlySet<FilterDimension>,
  searchIdsJson: string | undefined,
) {
  const filters = buildWhere(params, excluded, searchIdsJson);
  const rows = prepare(
    database,
    `
      select ${column} as value, count(*) as count
      from public_restaurants
      ${filters.sql}
      group by ${column}
    `,
  )
    .all(...filters.values) as FacetRow[];

  return rows
    .map(({ value, count }) => ({ value: value.trim(), count }))
    .filter(({ value }) => Boolean(value))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value, "ko-KR"));
}

function loadSearchIdsJson(database: DatabaseSync, query: string) {
  if (!query) {
    return undefined;
  }

  const normalizedQuery = query.toLocaleLowerCase("ko-KR");
  const cached = searchIdsCache.get(normalizedQuery);
  if (cached !== undefined) {
    searchIdsCache.delete(normalizedQuery);
    searchIdsCache.set(normalizedQuery, cached);
    return cached;
  }

  const rows = prepare(
    database,
    "select id from public_restaurants where instr(search_text, ?) > 0 order by id",
  )
    .all(normalizedQuery) as Array<{ id: number }>;
  const searchIdsJson = JSON.stringify(rows.map(({ id }) => id));

  searchIdsCache.set(normalizedQuery, searchIdsJson);
  if (searchIdsCache.size > MAX_SEARCH_CACHE_ENTRIES) {
    const oldestKey = searchIdsCache.keys().next().value;
    if (oldestKey !== undefined) {
      searchIdsCache.delete(oldestKey);
    }
  }

  return searchIdsJson;
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

function toRestaurantItem(row: PublicRestaurantRow): RestaurantItem {
  return {
    id: row.id,
    name: row.name,
    address: row.address,
    category: row.category,
    status: row.status,
    source: row.source,
    sourceTitle: row.source_title,
    sourceUrl: row.source_url,
    sourceThumbnailUrl: row.source_thumbnail_url,
    sourcePublishedAt: row.source_published_at,
    mapUrl: row.map_url,
    mustTasteItems: parseMustTasteItems(row.must_taste_json),
    region: {
      country: row.country,
      province: row.province,
      city: row.city,
      district: row.district,
      region: row.region,
      cluster: row.region_cluster,
    },
  };
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
          rawReason: normalizeText(String(entry.rawReason || "")),
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

function normalizeText(value: string | null) {
  return (value || "").replace(/\s+/g, " ").trim();
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

function normalizePositiveInteger(value: string | null, fallback: number) {
  if (!value) {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
