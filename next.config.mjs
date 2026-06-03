/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingIncludes: {
    "/": ["./data/tastyroad.sqlite"],
    "/api/restaurants": ["./data/tastyroad.sqlite"],
  },
};

export default nextConfig;
