/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    const sharedHeaders = [
      {
        key: "Cache-Control",
        value: "public, max-age=0, must-revalidate",
      },
      {
        key: "Vercel-Cache-Tag",
        value: "restaurants",
      },
    ];
    const browseCacheHeaders = [
      ...sharedHeaders,
      {
        key: "Vercel-CDN-Cache-Control",
        value: "public, s-maxage=3600, stale-while-revalidate=86400",
      },
    ];
    const searchCacheHeaders = [
      ...sharedHeaders,
      {
        key: "Vercel-CDN-Cache-Control",
        value: "public, s-maxage=60, stale-while-revalidate=300",
      },
    ];

    return ["/", "/api/restaurants"].flatMap((source) => [
      {
        source,
        missing: [{ type: "query", key: "q" }],
        headers: browseCacheHeaders,
      },
      {
        source,
        has: [{ type: "query", key: "q" }],
        headers: searchCacheHeaders,
      },
    ]);
  },
  outputFileTracingIncludes: {
    "/": ["./data/tastyroad-public.sqlite"],
    "/api/restaurants": ["./data/tastyroad-public.sqlite"],
  },
};

export default nextConfig;
