import { NextResponse } from "next/server";
import {
  normalizeRestaurantSearchParams,
  searchRestaurants,
} from "../../../lib/restaurants/query";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const url = new URL(request.url);
  const params = normalizeRestaurantSearchParams(url.searchParams);
  const response = searchRestaurants(params);

  return NextResponse.json(response);
}
