import type { NormalizedRegion } from "./region";

export type RestaurantSearchParams = {
  q: string;
  sources: string[];
  region: string;
  regionCluster: string;
  page: number;
  limit: number;
  includeFacets: boolean;
};

export type RestaurantItem = {
  id: number;
  name: string;
  address: string;
  category: string;
  status: string;
  source: string;
  sourceTitle: string;
  sourceUrl: string;
  mapUrl: string;
  storyHook: string;
  storyIntro: string;
  tastingFlow: string;
  region: NormalizedRegion;
};

export type FacetValue = {
  value: string;
  count: number;
};

export type RestaurantFacets = {
  sources: FacetValue[];
  regionClusters: FacetValue[];
  regions: FacetValue[];
};

export type RestaurantSearchResponse = {
  items: RestaurantItem[];
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  facets?: RestaurantFacets;
};
