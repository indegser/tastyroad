export type NormalizedRegion = {
  country: string;
  province: string;
  city: string;
  district: string;
  region: string;
  cluster: string;
};

type RegionInput = {
  region: string | null;
  address: string | null;
  countryCode: string | null;
};

const PROVINCE_ALIASES: Record<string, string> = {
  서울특별시: "서울",
  서울시: "서울",
  부산광역시: "부산",
  부산시: "부산",
  대구광역시: "대구",
  대구시: "대구",
  인천광역시: "인천",
  인천시: "인천",
  광주광역시: "광주",
  광주시: "광주",
  대전광역시: "대전",
  대전시: "대전",
  울산광역시: "울산",
  울산시: "울산",
  세종특별자치시: "세종",
  세종시: "세종",
  경기도: "경기",
  강원도: "강원",
  강원특별자치도: "강원",
  충청북도: "충북",
  충청남도: "충남",
  전라북도: "전북",
  전북특별자치도: "전북",
  전라남도: "전남",
  경상북도: "경북",
  경상남도: "경남",
  제주특별자치도: "제주",
};

const KOREAN_PROVINCES = new Set([
  "서울",
  "부산",
  "대구",
  "인천",
  "광주",
  "대전",
  "울산",
  "세종",
  "경기",
  "강원",
  "충북",
  "충남",
  "전북",
  "전남",
  "경북",
  "경남",
  "제주",
]);

const OVERSEAS_PATTERNS: Array<[RegExp, NormalizedRegion]> = [
  [
    /(?:일본|japan|tokyo|osaka|ginza|shinjuku|tsukiji|taito|minato|chuo)/i,
    overseas("일본", "일본 도쿄"),
  ],
  [/(?:홍콩|hong kong|central|taikoo|ifc mall)/i, overseas("홍콩", "홍콩")],
  [
    /(?:싱가포르|singapore|rangoon|lau pa sat)/i,
    overseas("싱가포르", "싱가포르"),
  ],
  [/(?:berlin|germany|독일)/i, overseas("독일", "독일")],
];

export function normalizeRegion(input: RegionInput): NormalizedRegion {
  const address = normalizeSpacing(input.address);
  const rawRegion = normalizeSpacing(input.region);
  const countryCode = normalizeSpacing(input.countryCode).toUpperCase();
  const domestic = parseDomestic(address) || parseDomestic(rawRegion);

  if (domestic) {
    return domestic;
  }

  const overseasRegion = parseOverseas(`${address} ${rawRegion}`);
  if (overseasRegion) {
    return overseasRegion;
  }

  if (countryCode && countryCode !== "KR") {
    return {
      country: countryCode,
      province: "",
      city: "",
      district: "",
      region: "해외",
      cluster: "해외",
    };
  }

  return {
    country: "한국",
    province: "",
    city: "",
    district: "",
    region: rawRegion && isUsableRegion(rawRegion) ? rawRegion : "미분류",
    cluster: "미분류",
  };
}

function parseDomestic(value: string): NormalizedRegion | null {
  const parts = value.split(" ").filter(Boolean);
  if (parts.length === 0) {
    return null;
  }

  const province = normalizeProvince(parts[0]);
  if (!KOREAN_PROVINCES.has(province)) {
    return null;
  }

  const cityOrDistrict = parts[1] || "";
  const district =
    province === "서울"
      ? cityOrDistrict.endsWith("구")
        ? cityOrDistrict
        : ""
      : parts.find((part) => part.endsWith("구")) || "";
  const city =
    province === "서울"
      ? ""
      : cityOrDistrict && /(?:시|군)$/.test(cityOrDistrict)
        ? cityOrDistrict
        : "";
  const region =
    province === "서울" && district
      ? `${province} ${district}`
      : city
        ? `${province} ${city}`
        : province;

  return {
    country: "한국",
    province,
    city,
    district,
    region,
    cluster: province,
  };
}

function normalizeProvince(value: string) {
  return PROVINCE_ALIASES[value] || value;
}

function parseOverseas(value: string) {
  for (const [pattern, region] of OVERSEAS_PATTERNS) {
    if (pattern.test(value)) {
      return region;
    }
  }

  return null;
}

function overseas(country: string, region: string): NormalizedRegion {
  return {
    country,
    province: "",
    city: "",
    district: "",
    region,
    cluster: "해외",
  };
}

function normalizeSpacing(value: string | null | undefined) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function isUsableRegion(value: string) {
  return !/^\d|층|\/F|chome|chõme|chöme|tokyo/i.test(value);
}
