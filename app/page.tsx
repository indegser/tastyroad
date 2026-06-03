import {
  normalizeRestaurantSearchParams,
  searchRestaurants,
} from "../lib/restaurants/query";
import type { FacetValue } from "../lib/restaurants/types";

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
      <header>
        <p className="muted">검증된 맛집 {result.total.toLocaleString("ko-KR")}곳</p>
        <h1>맛집 탐색</h1>
        <p className="summary muted">
          스토리와 지도 매핑이 모두 완료된 맛집을 출처와 지역으로 좁혀 볼 수 있습니다.
        </p>
      </header>

      {facets ? (
        <aside className="facet-panel" aria-label="맛집 필터">
          <div className="facet-header">
            <strong>필터</strong>
            {hasActiveFilters(params) ? (
              <a href="/" className="clear-filters">
                전체 보기
              </a>
            ) : null}
          </div>
          <FacetGroup
            label="지역권"
            values={facets.regionClusters}
            activeValue={params.regionCluster}
            hrefFor={(value) =>
              hrefWith(rawSearchParams, {
                regionCluster: value,
                region: "",
                page: "",
              })
            }
          />
          <FacetGroup
            label="세부 지역"
            values={facets.regions}
            activeValue={params.region}
            hrefFor={(value) => hrefWith(rawSearchParams, { region: value, page: "" })}
          />
          <FacetGroup
            label="출처"
            values={facets.sources}
            activeValue={params.source}
            hrefFor={(value) => hrefWith(rawSearchParams, { source: value, page: "" })}
          />
        </aside>
      ) : null}

      {result.items.length > 0 ? (
        <ol className="video-list">
          {result.items.map((restaurant) => (
            <li key={restaurant.id}>
              <article className="video-card">
                <div className="video-info">
                  <h2>{restaurant.name}</h2>
                  <dl className="info-table">
                    <div className="info-row">
                      <dt>지역</dt>
                      <dd>
                        {restaurant.region.region}
                        <span className="subtle-divider">/</span>
                        {restaurant.region.cluster}
                      </dd>
                    </div>
                    <div className="info-row">
                      <dt>주소</dt>
                      <dd>{restaurant.address}</dd>
                    </div>
                    <div className="info-row">
                      <dt>채널</dt>
                      <dd>{restaurant.source}</dd>
                    </div>
                    <div className="info-row">
                      <dt>영상</dt>
                      <dd>
                        <a className="video-link" href={restaurant.sourceUrl}>
                          <span>{restaurant.sourceTitle}</span>
                          <span aria-hidden="true">↗</span>
                        </a>
                      </dd>
                    </div>
                    {restaurant.mapUrl ? (
                      <div className="info-row">
                        <dt>지도</dt>
                        <dd>
                          <a className="video-link" href={restaurant.mapUrl}>
                            <span>지도에서 보기</span>
                            <span aria-hidden="true">↗</span>
                          </a>
                        </dd>
                      </div>
                    ) : null}
                    {restaurant.storyHook ? (
                      <div className="info-row">
                        <dt>한줄 요약</dt>
                        <dd>{restaurant.storyHook}</dd>
                      </div>
                    ) : null}
                  </dl>
                  {restaurant.storyIntro ? (
                    <section className="story-section" aria-label="이야기">
                      <h3 className="section-label">이야기</h3>
                      <p>{restaurant.storyIntro}</p>
                    </section>
                  ) : null}
                  {restaurant.tastingFlow ? (
                    <section className="tasting-flow" aria-label="시식 메뉴 및 순서">
                      <h3 className="section-label">시식 메뉴 및 순서</h3>
                      <p>{restaurant.tastingFlow}</p>
                    </section>
                  ) : null}
                </div>
              </article>
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
    </main>
  );
}

function FacetGroup({
  label,
  values,
  activeValue,
  hrefFor,
}: {
  label: string;
  values: FacetValue[];
  activeValue: string;
  hrefFor: (value: string) => string;
}) {
  if (values.length === 0) {
    return null;
  }

  return (
    <section className="facet-group">
      <h2>{label}</h2>
      <div className="facet-options">
        {values.map((facet) => {
          const active = facet.value === activeValue;

          return (
            <a
              key={facet.value}
              href={active ? hrefFor("") : hrefFor(facet.value)}
              className={active ? "is-active" : undefined}
              aria-current={active ? "true" : undefined}
            >
              <span>{facet.value}</span>
              <small>{facet.count.toLocaleString("ko-KR")}</small>
            </a>
          );
        })}
      </div>
    </section>
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
        <a href={hrefWith(searchParams, { page: String(page - 1) })}>이전</a>
      ) : (
        <span>이전</span>
      )}
      <strong>
        {page.toLocaleString("ko-KR")} / {totalPages.toLocaleString("ko-KR")}
      </strong>
      {page < totalPages ? (
        <a href={hrefWith(searchParams, { page: String(page + 1) })}>다음</a>
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
      if (value[0]) {
        urlParams.set(key, value[0]);
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

function hasActiveFilters(params: {
  source: string;
  region: string;
  regionCluster: string;
}) {
  return Boolean(params.source || params.region || params.regionCluster);
}
