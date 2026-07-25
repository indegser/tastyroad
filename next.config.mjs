/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingIncludes: {
    "/": ["./data/tastyroad-public.sqlite"],
    "/api/restaurants": ["./data/tastyroad-public.sqlite"],
  },
};

export default nextConfig;
