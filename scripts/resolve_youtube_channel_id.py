#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import urllib.request
from urllib.parse import quote, urlsplit, urlunsplit


def fetch_html(url: str) -> str:
    url = quote_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "tastyroad-channel-resolver/0.1 (+https://youtube.com)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def quote_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(parts.path, safe="/@"),
            quote(parts.query, safe="=&?/:@%+"),
            quote(parts.fragment, safe=""),
        )
    )


def resolve_channel_id(url: str) -> str:
    html = fetch_html(url)
    patterns = [
        r'"channelId":"(UC[^"]+)"',
        r'"externalId":"(UC[^"]+)"',
        r'<meta itemprop="channelId" content="(UC[^"]+)">',
        r'https://www\.youtube\.com/channel/(UC[^"?/]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    raise RuntimeError(f"Could not resolve channel id from {url}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a YouTube channel id from a channel URL or handle URL.")
    parser.add_argument("url", help="Example: https://www.youtube.com/@somehandle")
    args = parser.parse_args()

    channel_id = resolve_channel_id(args.url)
    print(channel_id)
    print(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
