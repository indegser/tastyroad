import { normalizeRegion as normalizeRegionRuntime } from "./region-runtime.mjs";

export type NormalizedRegion = {
  country: string;
  province: string;
  city: string;
  district: string;
  region: string;
  cluster: string;
};

export type RegionInput = {
  region: string | null;
  address: string | null;
  countryCode: string | null;
};

export function normalizeRegion(input: RegionInput): NormalizedRegion {
  return normalizeRegionRuntime(input) as NormalizedRegion;
}
