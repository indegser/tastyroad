import type { NormalizedRegion } from "./region";

export type RestaurantSearchParams = {
  q: string;
  sources: string[];
  region: string;
  regionCluster: string;
  nameInitial: string;
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
  sourceThumbnailUrl: string;
  sourcePublishedAt: string;
  mapUrl: string;
  mustTasteItems: MustTasteItem[];
  region: NormalizedRegion;
};

export type MustTasteItem = {
  rank: number;
  menuItem: string;
  reason: string;
  timestamp: string;
  evidence: string;
};

export type FacetValue = {
  value: string;
  count: number;
};

export type RestaurantFacets = {
  nameInitials: FacetValue[];
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
