import { DatabaseSync } from "node:sqlite";
import { renameSync, rmSync, statSync } from "node:fs";
import path from "node:path";
import { normalizeRegion } from "./region-runtime.mjs";

const SOURCE_PATH = path.join(process.cwd(), "data/tastyroad.sqlite");
const TARGET_PATH = path.join(process.cwd(), "data/tastyroad-public.sqlite");
const TEMP_PATH = `${TARGET_PATH}.tmp-${process.pid}`;

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
const HANGUL_INITIAL_GROUPS = {
  "ㄲ": "ㄱ",
  "ㄸ": "ㄷ",
  "ㅃ": "ㅂ",
  "ㅆ": "ㅅ",
  "ㅉ": "ㅈ",
};
const HANGUL_SYLLABLE_START = 0xac00;
const HANGUL_SYLLABLE_END = 0xd7a3;
const HANGUL_SYLLABLES_PER_INITIAL = 588;

const source = new DatabaseSync(SOURCE_PATH, { readOnly: true });
rmSync(TEMP_PATH, { force: true });
const target = new DatabaseSync(TEMP_PATH);
let buildSucceeded = false;

try {
  const rows = source
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
                  'reason', coalesce(nullif(repaired_reason, ''), reason),
                  'rawReason', reason,
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
                repaired_reason,
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
    .all();

  target.exec(`
    pragma journal_mode = off;
    pragma synchronous = off;
    pragma temp_store = memory;

    create table public_restaurants (
      id integer primary key,
      name text not null,
      address text not null,
      category text not null,
      status text not null,
      source text not null,
      source_title text not null,
      source_url text not null,
      source_thumbnail_url text not null,
      source_published_at text not null,
      map_url text not null,
      must_taste_json text not null,
      country text not null,
      province text not null,
      city text not null,
      district text not null,
      region text not null,
      region_cluster text not null,
      name_initial text not null,
      search_text text not null,
      sort_rank integer not null unique
    );

    create index public_restaurants_source_idx
      on public_restaurants(source, sort_rank);
    create index public_restaurants_region_idx
      on public_restaurants(region_cluster, region, sort_rank);
    create index public_restaurants_name_initial_idx
      on public_restaurants(name_initial, sort_rank);
  `);

  const insert = target.prepare(`
    insert into public_restaurants (
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
      region_cluster,
      name_initial,
      search_text,
      sort_rank
    ) values (${Array.from({ length: 21 }, () => "?").join(", ")})
  `);

  target.exec("begin immediate");
  for (const [index, rawRow] of rows.entries()) {
    const row = rawRow;
    const mustTasteItems = parseMustTasteItems(asNullableString(row.must_taste_json));
    const region = normalizeRegion({
      region: asNullableString(row.raw_region),
      address: asString(row.address),
      countryCode: asString(row.country_code),
    });
    const item = {
      name: asString(row.name),
      address: asString(row.address),
      category: asString(row.category),
      source: asString(row.source),
      sourceTitle: asString(row.source_title),
      mustTasteItems,
      region,
    };

    insert.run(
      Number(row.id),
      item.name,
      item.address,
      item.category,
      asString(row.status),
      item.source,
      asString(row.source_title),
      asString(row.source_url),
      asString(row.source_thumbnail_url),
      asString(row.source_published_at),
      asString(row.map_url),
      JSON.stringify(mustTasteItems),
      region.country,
      region.province,
      region.city,
      region.district,
      region.region,
      region.cluster,
      getRestaurantNameInitial(item.name),
      buildRestaurantSearchText(item),
      index,
    );
  }
  target.exec("commit");
  target.exec("vacuum");
  buildSucceeded = true;
} catch (error) {
  try {
    target.exec("rollback");
  } catch {
    // No transaction was active.
  }
  throw error;
} finally {
  source.close();
  target.close();
  if (!buildSucceeded) {
    rmSync(TEMP_PATH, { force: true });
  }
}

renameSync(TEMP_PATH, TARGET_PATH);

const sizeMb = statSync(TARGET_PATH).size / 1024 / 1024;
console.log(
  `Built ${path.relative(process.cwd(), TARGET_PATH)} with ${getPublicCount()} restaurants (${sizeMb.toFixed(2)} MB).`,
);

function getPublicCount() {
  const database = new DatabaseSync(TARGET_PATH, { readOnly: true });
  try {
    const row = database
      .prepare("select count(*) as count from public_restaurants")
      .get();
    return row.count;
  } finally {
    database.close();
  }
}

function buildRestaurantSearchText(item) {
  return [
    item.name,
    item.address,
    item.category,
    item.source,
    item.sourceTitle,
    ...item.mustTasteItems.flatMap((mustTasteItem) => [
      mustTasteItem.menuItem,
      mustTasteItem.reason,
      mustTasteItem.rawReason,
      mustTasteItem.timestamp,
      mustTasteItem.evidence,
    ]),
    item.region.region,
    item.region.cluster,
  ]
    .join(" ")
    .toLocaleLowerCase("ko-KR");
}

function parseMustTasteItems(value) {
  if (!value) {
    return [];
  }

  try {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }
        const entry = item;
        return {
          rank: normalizePositiveInteger(String(entry.rank || ""), 0),
          menuItem: normalizeText(String(entry.menuItem || "")),
          reason: normalizeText(String(entry.reason || "")),
          rawReason: normalizeText(String(entry.rawReason || "")),
          timestamp: normalizeText(String(entry.timestamp || "")),
          evidence: normalizeText(String(entry.evidence || "")),
        };
      })
      .filter((item) => {
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

function getRestaurantNameInitial(name) {
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

function normalizeText(value) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function normalizePositiveInteger(value, fallback) {
  if (!value) {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function asString(value) {
  return value == null ? "" : String(value);
}

function asNullableString(value) {
  return value == null ? null : String(value);
}
