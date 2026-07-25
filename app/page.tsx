import Link from "next/link";
import {
  normalizeRestaurantSearchParams,
  searchRestaurants,
} from "../lib/restaurants/query";
import type {
  FacetValue,
  RestaurantItem,
  RestaurantSearchParams,
} from "../lib/restaurants/types";

type PageSearchParams = Record<string, string | string[] | undefined>;

export const dynamic = "force-dynamic";

const PAGE_SIZE = 20;

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<PageSearchParams>;
}) {
  const rawSearchParams = await searchParams;
  const urlParams = toUrlSearchParams(rawSearchParams);
  urlParams.set("includeFacets", "true");
  urlParams.set("limit", String(PAGE_SIZE));

  const params = normalizeRestaurantSearchParams(urlParams);
  const result = searchRestaurants(params);
  const facets = result.facets;

  return (
    <main>
      <header className="page-header">
        <p className="muted">{result.total.toLocaleString("ko-KR")}곳</p>
        <h1>맛집 탐색</h1>
      </header>

      <SearchForm params={params} />
      <ActiveFilters params={params} searchParams={rawSearchParams} />

      <div className="explorer-layout">
        {facets ? (
          <aside className="facet-panel" aria-label="탐색 조건">
            <div className="facet-groups">
              <FacetGroup
                label="가나다"
                values={facets.nameInitials}
                activeValue={params.nameInitial}
                hrefFor={(value) =>
                  hrefWith(rawSearchParams, { nameInitial: value, page: "" })
                }
                variant="initials"
              />
              <RegionFacetGroup
                regionClusters={facets.regionClusters}
                regions={facets.regions}
                activeRegionCluster={params.regionCluster}
                activeRegion={params.region}
                hrefForRegionCluster={(value) =>
                  hrefWith(rawSearchParams, {
                    regionCluster: value,
                    region: "",
                    page: "",
                  })
                }
                hrefForRegion={(value) =>
                  hrefWith(rawSearchParams, { region: value, page: "" })
                }
              />
              <FacetGroup
                label="채널"
                values={facets.sources}
                activeValues={params.sources}
                hrefFor={(value) => hrefWithToggledValue(rawSearchParams, "source", value)}
                multi
              />
            </div>
          </aside>
        ) : null}

        <section className="results-panel" aria-labelledby="results-heading">
          <div className="results-header">
            <h2 id="results-heading" className="visually-hidden">
              맛집 목록
            </h2>
            <p>{getResultSummary(result.total, params)}</p>
          </div>

          {result.items.length > 0 ? (
            <ol className="restaurant-list">
              {result.items.map((restaurant) => (
                <li key={restaurant.id}>
                  <RestaurantCard restaurant={restaurant} />
                </li>
              ))}
            </ol>
          ) : (
            <p className="empty-state">조건에 맞는 맛집이 없습니다.</p>
          )}

          <Pagination
            page={result.page}
            totalPages={result.totalPages}
            searchParams={rawSearchParams}
          />
        </section>
      </div>
    </main>
  );
}

function RestaurantCard({ restaurant }: { restaurant: RestaurantItem }) {
  const uploadAge = getRelativeUploadAge(restaurant.sourcePublishedAt);
  const summaryClassName = restaurant.sourceThumbnailUrl
    ? "restaurant-summary"
    : "restaurant-summary is-text-only";

  return (
    <article className="restaurant-card">
      <div className={summaryClassName}>
        <div className="restaurant-info">
          <h3>{restaurant.name}</h3>
          <a className="video-link" href={restaurant.sourceUrl}>
            <span>{restaurant.sourceTitle}</span>
            <span aria-hidden="true">↗</span>
          </a>
          <p className="source-meta">
            {restaurant.source}
            {uploadAge ? ` · ${uploadAge}` : ""}
          </p>
          <p className="restaurant-address">
            {restaurant.mapUrl ? (
              <a
                className="address-map-link"
                href={restaurant.mapUrl}
                aria-label={`${restaurant.address} 지도에서 보기`}
                title={restaurant.address}
              >
                <span>{restaurant.address}</span>
                <span className="map-link-label">
                  지도
                  <span aria-hidden="true">↗</span>
                </span>
              </a>
            ) : (
              <span className="restaurant-address-text" title={restaurant.address}>
                {restaurant.address}
              </span>
            )}
          </p>
        </div>

        {restaurant.sourceThumbnailUrl ? (
          <a
            className="video-thumbnail-link"
            href={restaurant.sourceUrl}
            aria-label={`영상 보기: ${restaurant.sourceTitle}`}
          >
            <img
              src={restaurant.sourceThumbnailUrl}
              alt=""
              loading="lazy"
              decoding="async"
            />
          </a>
        ) : null}
      </div>

      {restaurant.mustTasteItems.length > 0 ? (
        <section className="must-taste-section" aria-label="추천 메뉴">
          <ol className="must-taste-list">
            {restaurant.mustTasteItems.map((item) => (
              <li key={`${item.rank}-${item.menuItem}`}>
                <span className="must-taste-rank" aria-label={`${item.rank}순위`}>
                  {item.rank}
                </span>
                <div className="must-taste-body">
                  <div className="must-taste-heading">
                    <strong>{item.menuItem}</strong>
                    <time>{item.timestamp}</time>
                  </div>
                  <p>“{item.reason}”</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
    </article>
  );
}

function SearchForm({ params }: { params: RestaurantSearchParams }) {
  return (
    <form className="search-form" action="/" role="search">
      {params.nameInitial ? (
        <input type="hidden" name="nameInitial" value={params.nameInitial} />
      ) : null}
      {params.regionCluster ? (
        <input type="hidden" name="regionCluster" value={params.regionCluster} />
      ) : null}
      {params.region ? (
        <input type="hidden" name="region" value={params.region} />
      ) : null}
      {params.sources.map((source) => (
        <input key={source} type="hidden" name="source" value={source} />
      ))}
      <label className="visually-hidden" htmlFor="restaurant-search">
        맛집 검색
      </label>
      <input
        id="restaurant-search"
        type="search"
        name="q"
        defaultValue={params.q}
        placeholder="식당명, 동네, 메뉴, 채널"
        autoComplete="off"
      />
      <button type="submit">검색</button>
    </form>
  );
}

function ActiveFilters({
  params,
  searchParams,
}: {
  params: RestaurantSearchParams;
  searchParams: PageSearchParams | undefined;
}) {
  const filters = getActiveFilters(params, searchParams);

  if (filters.length === 0) {
    return null;
  }

  return (
    <nav className="active-filters" aria-label="선택한 조건">
      {filters.map((filter) => (
        <Link
          key={`${filter.label}:${filter.value}`}
          href={filter.href}
          prefetch={false}
          aria-label={`${filter.label} ${filter.value} 제거`}
        >
          <span>{filter.value}</span>
          <b aria-hidden="true">x</b>
        </Link>
      ))}
      <Link className="clear-all" href="/" prefetch={false} aria-label="모든 조건 제거">
        초기화
      </Link>
    </nav>
  );
}

function FacetGroup({
  label,
  values,
  activeValue,
  activeValues,
  hrefFor,
  multi = false,
  variant = "list",
}: {
  label: string;
  values: FacetValue[];
  activeValue?: string;
  activeValues?: string[];
  hrefFor: (value: string) => string;
  multi?: boolean;
  variant?: "list" | "initials";
}) {
  if (values.length === 0) {
    return null;
  }

  const activeCount = values.filter((facet) =>
    activeValues ? activeValues.includes(facet.value) : facet.value === activeValue,
  ).length;

  return (
    <details className={`facet-group ${variant === "initials" ? "is-initials" : ""}`}>
      <summary>
        <span>{label}</span>
        <small>{activeCount > 0 ? `${activeCount} 선택` : `${values.length}개`}</small>
      </summary>
      <div className="facet-options">
        {values.map((facet) => {
          const active = activeValues
            ? activeValues.includes(facet.value)
            : facet.value === activeValue;

          return (
            <Link
              key={facet.value}
              href={multi || !active ? hrefFor(facet.value) : hrefFor("")}
              prefetch={false}
              className={`facet-option ${active ? "is-active" : ""}`}
              aria-current={active ? "true" : undefined}
            >
              <span className="facet-marker" aria-hidden="true" />
              <span className="facet-option-label">{facet.value}</span>
              <small>{facet.count.toLocaleString("ko-KR")}</small>
            </Link>
          );
        })}
      </div>
    </details>
  );
}

function RegionFacetGroup({
  regionClusters,
  regions,
  activeRegionCluster,
  activeRegion,
  hrefForRegionCluster,
  hrefForRegion,
}: {
  regionClusters: FacetValue[];
  regions: FacetValue[];
  activeRegionCluster: string;
  activeRegion: string;
  hrefForRegionCluster: (value: string) => string;
  hrefForRegion: (value: string) => string;
}) {
  if (regionClusters.length === 0) {
    return null;
  }

  const activeCount = Number(Boolean(activeRegionCluster)) + Number(Boolean(activeRegion));

  return (
    <details className="facet-group is-region">
      <summary>
        <span>지역</span>
        <small>{activeCount > 0 ? `${activeCount} 선택` : `${regionClusters.length}개`}</small>
      </summary>
      <div className="facet-options">
        <section className="facet-option-section" aria-label="시도">
          <h3>시도</h3>
          <div className="facet-option-list">
            {regionClusters.map((facet) => {
              const active = facet.value === activeRegionCluster;

              return (
                <Link
                  key={facet.value}
                  href={active ? hrefForRegionCluster("") : hrefForRegionCluster(facet.value)}
                  prefetch={false}
                  className={`facet-option ${active ? "is-active" : ""}`}
                  aria-current={active ? "true" : undefined}
                >
                  <span className="facet-marker" aria-hidden="true" />
                  <span className="facet-option-label">{facet.value}</span>
                  <small>{facet.count.toLocaleString("ko-KR")}</small>
                </Link>
              );
            })}
          </div>
        </section>

        {activeRegionCluster || activeRegion ? (
          <section className="facet-option-section" aria-label="시군구">
            <h3>시군구</h3>
            <div className="facet-option-list">
              {regions.map((facet) => {
                const active = facet.value === activeRegion;

                return (
                  <Link
                    key={facet.value}
                    href={active ? hrefForRegion("") : hrefForRegion(facet.value)}
                    prefetch={false}
                    className={`facet-option ${active ? "is-active" : ""}`}
                    aria-current={active ? "true" : undefined}
                  >
                    <span className="facet-marker" aria-hidden="true" />
                    <span className="facet-option-label">{facet.value}</span>
                    <small>{facet.count.toLocaleString("ko-KR")}</small>
                  </Link>
                );
              })}
            </div>
          </section>
        ) : null}
      </div>
    </details>
  );
}

function Pagination({
  page,
  totalPages,
  searchParams,
}: {
  page: number;
  totalPages: number;
  searchParams: PageSearchParams | undefined;
}) {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav className="pagination" aria-label="페이지">
      {page > 1 ? (
        <Link
          href={hrefWith(searchParams, { page: String(page - 1) })}
          prefetch={false}
        >
          이전
        </Link>
      ) : (
        <span>이전</span>
      )}
      <strong>
        {page.toLocaleString("ko-KR")} / {totalPages.toLocaleString("ko-KR")}
      </strong>
      {page < totalPages ? (
        <Link
          href={hrefWith(searchParams, { page: String(page + 1) })}
          prefetch={false}
        >
          다음
        </Link>
      ) : (
        <span>다음</span>
      )}
    </nav>
  );
}

function toUrlSearchParams(searchParams: PageSearchParams | undefined) {
  const urlParams = new URLSearchParams();

  for (const [key, value] of Object.entries(searchParams || {})) {
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item) {
          urlParams.append(key, item);
        }
      }
      continue;
    }
    if (value) {
      urlParams.set(key, value);
    }
  }

  return urlParams;
}

function hrefWith(
  searchParams: PageSearchParams | undefined,
  updates: Record<string, string>,
) {
  const urlParams = toUrlSearchParams(searchParams);

  for (const [key, value] of Object.entries(updates)) {
    if (value) {
      urlParams.set(key, value);
    } else {
      urlParams.delete(key);
    }
  }

  const query = urlParams.toString();
  return query ? `/?${query}` : "/";
}

function hrefWithToggledValue(
  searchParams: PageSearchParams | undefined,
  key: string,
  value: string,
) {
  const urlParams = toUrlSearchParams(searchParams);
  const values = Array.from(
    new Set(
      urlParams
        .getAll(key)
        .flatMap((item) => item.split(","))
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  );
  urlParams.delete(key);

  for (const currentValue of values) {
    if (currentValue !== value) {
      urlParams.append(key, currentValue);
    }
  }

  if (!values.includes(value)) {
    urlParams.append(key, value);
  }

  urlParams.delete("page");

  const query = urlParams.toString();
  return query ? `/?${query}` : "/";
}

function getActiveFilters(
  params: RestaurantSearchParams,
  searchParams: PageSearchParams | undefined,
) {
  const filters: Array<{ label: string; value: string; href: string }> = [];

  if (params.q) {
    filters.push({
      label: "검색어",
      value: params.q,
      href: hrefWith(searchParams, { q: "", page: "" }),
    });
  }
  if (params.nameInitial) {
    filters.push({
      label: "가나다",
      value: params.nameInitial,
      href: hrefWith(searchParams, { nameInitial: "", page: "" }),
    });
  }
  if (params.regionCluster) {
    filters.push({
      label: "시도",
      value: params.regionCluster,
      href: hrefWith(searchParams, { regionCluster: "", region: "", page: "" }),
    });
  }
  if (params.region) {
    filters.push({
      label: "시군구",
      value: params.region,
      href: hrefWith(searchParams, { region: "", page: "" }),
    });
  }

  for (const source of params.sources) {
    filters.push({
      label: "채널",
      value: source,
      href: hrefWithToggledValue(searchParams, "source", source),
    });
  }

  return filters;
}

function getResultSummary(total: number, params: RestaurantSearchParams) {
  const activeLabels = [
    params.q ? `"${params.q}"` : "",
    params.nameInitial ? `${params.nameInitial} 초성` : "",
    params.regionCluster,
    params.region,
    ...params.sources,
  ].filter(Boolean);
  const totalLabel = `${total.toLocaleString("ko-KR")}곳`;

  return activeLabels.length > 0
    ? `${totalLabel} · ${activeLabels.join(" · ")}`
    : totalLabel;
}

function getRelativeUploadAge(value: string) {
  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) {
    return "";
  }

  const elapsedSeconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));

  if (elapsedSeconds < 60) {
    return "방금 전";
  }

  const units = [
    { seconds: 365 * 24 * 60 * 60, label: "년" },
    { seconds: 30 * 24 * 60 * 60, label: "개월" },
    { seconds: 7 * 24 * 60 * 60, label: "주" },
    { seconds: 24 * 60 * 60, label: "일" },
    { seconds: 60 * 60, label: "시간" },
    { seconds: 60, label: "분" },
  ];

  for (const unit of units) {
    const count = Math.floor(elapsedSeconds / unit.seconds);

    if (count > 0) {
      return `${count}${unit.label} 전`;
    }
  }

  return "방금 전";
}
