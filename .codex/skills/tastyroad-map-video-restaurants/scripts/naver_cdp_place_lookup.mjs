#!/usr/bin/env node

import { createRequire } from "node:module";
import fs from "node:fs/promises";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const NAVER_PLACE_ID_RE = /(?:\/entry\/place\/|\/place\/|\/restaurant\/|\/cafe\/)(\d+)/;

function parseArgs(argv) {
  const args = {
    port: "9222",
    input: "",
    output: "",
    delayMs: 2200,
    timeoutMs: 30000,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--port") args.port = argv[++i];
    else if (arg === "--input") args.input = argv[++i];
    else if (arg === "--output") args.output = argv[++i];
    else if (arg === "--delay-ms") args.delayMs = Number(argv[++i]);
    else if (arg === "--timeout-ms") args.timeoutMs = Number(argv[++i]);
    else throw new Error(`Unknown argument: ${arg}`);
  }

  if (!args.input) throw new Error("--input is required");
  if (!args.output) throw new Error("--output is required");
  return args;
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function extractPlaceId(value) {
  if (!value) return "";
  const match = NAVER_PLACE_ID_RE.exec(value);
  return match ? match[1] : "";
}

async function evaluateFrame(frame, expression, fallback) {
  try {
    return await frame.evaluate(expression);
  } catch {
    return fallback;
  }
}

async function collectEvidence(page) {
  const urls = [page.url(), ...page.frames().map((frame) => frame.url())];
  const hrefs = [];
  const frameTexts = [];

  for (const frame of page.frames()) {
    const frameHrefs = await evaluateFrame(
      frame,
      () => Array.from(document.querySelectorAll("a[href]"), (anchor) => anchor.href).slice(0, 80),
      [],
    );
    hrefs.push(...frameHrefs);

    const text = await evaluateFrame(
      frame,
      () => document.body?.innerText || "",
      "",
    );
    if (text) {
      frameTexts.push({
        url: frame.url(),
        text: text.split("\n").filter(Boolean).slice(0, 80).join("\n"),
      });
    }
  }

  const placeId = [...urls, ...hrefs].map(extractPlaceId).find(Boolean) || "";
  return { urls, hrefs: hrefs.slice(0, 80), placeId, frameTexts };
}

function classifyDetailPath(text) {
  if (/카페|베이커리|디저트|제과|빵집/.test(text)) return "restaurant";
  return "restaurant";
}

function parseDetailText(text) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !line.includes("browser-mcp-container"));

  const addressMarker = lines.findIndex((line) => line === "주소");
  const address =
    addressMarker >= 0 && lines[addressMarker + 1]
      ? lines[addressMarker + 1]
      : lines.find((line) => /(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주).*(시|군|구|로|길)/.test(line)) || "";

  const phone = lines.find((line) => /(?:\d{2,4}-\d{3,4}-\d{4}|0507-\d{4}-\d{4})/.test(line)) || "";
  const name =
    lines.find((line, index) => {
      if (index === 0 && line === "이전 페이지") return false;
      return !/^(홈|소식|메뉴|리뷰|사진|지도|주변|저장|공유|길찾기|출발|도착|페이지 닫기)$/.test(line);
    }) || "";
  const categoryIndex = lines.findIndex((line) => line === name);
  const category =
    categoryIndex >= 0
      ? lines
          .slice(categoryIndex + 1, categoryIndex + 5)
          .find((line) => !/별점|방문자리뷰|블로그리뷰|리뷰|저장|길찾기|공유/.test(line)) || ""
      : "";

  return {
    name,
    category,
    address,
    phone,
    lines: lines.slice(0, 120),
  };
}

async function clickSearchResult(page, item, query, args) {
  const clickText = item.click_text || item.expected_name || query.split(/\s+/)[0];
  if (!clickText) return false;

  for (const frame of page.frames()) {
    const locator = frame.locator("a, button, [role='button']").filter({ hasText: clickText }).first();
    try {
      if (await locator.count()) {
        await locator.click({ timeout: 3000 });
        await sleep(args.delayMs);
        return true;
      }
    } catch {
      // Try the next frame; Naver search result frames change shape frequently.
    }
  }

  return false;
}

async function lookupOne(context, item, args) {
  const page = await context.newPage();
  const query = item.query || item.name;
  if (!query) throw new Error("Each input item needs query or name");

  const searchUrl = `https://map.naver.com/p/search/${encodeURIComponent(query)}`;
  await page.goto(searchUrl, { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
  await sleep(args.delayMs);

  let evidence = await collectEvidence(page);
  let placeId = evidence.placeId;

  if (!placeId) {
    await sleep(args.delayMs);
    evidence = await collectEvidence(page);
    placeId = evidence.placeId;
  }

  if (!placeId && (await clickSearchResult(page, item, query, args))) {
    evidence = await collectEvidence(page);
    placeId = evidence.placeId;
  }

  let detail = null;
  if (placeId) {
    const detailKind = classifyDetailPath("");
    const detailUrl = `https://pcmap.place.naver.com/${detailKind}/${placeId}/home`;
    await page.goto(detailUrl, { waitUntil: "domcontentloaded", timeout: args.timeoutMs }).catch(() => {});
    await sleep(1200);
    const detailText = await page.evaluate(() => document.body?.innerText || "").catch(() => "");
    detail = {
      url: page.url(),
      ...parseDetailText(detailText),
    };
  }

  await page.close();
  return {
    ...item,
    query,
    search_url: searchUrl,
    place_id: placeId,
    map_url: placeId ? `https://map.naver.com/p/entry/place/${placeId}?placePath=%2Fhome` : "",
    detail,
    evidence,
    looked_up_at: new Date().toISOString(),
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const raw = await fs.readFile(args.input, "utf8");
  const items = JSON.parse(raw);
  if (!Array.isArray(items)) throw new Error("Input must be a JSON array");

  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${args.port}`);
  const context = browser.contexts()[0] || (await browser.newContext());
  const results = [];

  for (const item of items) {
    try {
      const result = await lookupOne(context, item, args);
      results.push(result);
      await fs.writeFile(args.output, `${JSON.stringify(results, null, 2)}\n`, "utf8");
      console.log(`${result.place_id ? "ok" : "miss"}\t${result.query}\t${result.place_id}`);
    } catch (error) {
      results.push({
        ...item,
        error: error instanceof Error ? error.message : String(error),
        looked_up_at: new Date().toISOString(),
      });
      await fs.writeFile(args.output, `${JSON.stringify(results, null, 2)}\n`, "utf8");
      console.log(`error\t${item.query || item.name || ""}\t${error instanceof Error ? error.message : error}`);
    }
  }

  await fs.writeFile(args.output, `${JSON.stringify(results, null, 2)}\n`, "utf8");
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
