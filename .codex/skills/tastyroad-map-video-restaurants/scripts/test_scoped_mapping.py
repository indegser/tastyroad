from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


def load_script(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


backlog = load_script("process_pipeline_backlog")
resolver = load_script("resolve_naver_search_candidates")


class ScopedMappingTests(unittest.TestCase):
    def test_backlog_processes_only_requested_video_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sqlite_path = Path(directory) / "test.sqlite"
            with sqlite3.connect(sqlite_path) as connection:
                connection.executescript(
                    """
                    create table youtube_videos (
                      id integer primary key,
                      description text
                    );
                    create table pipeline_rows (
                      youtube_video_id integer,
                      video_id text,
                      title text,
                      url text,
                      review_status text,
                      mapping_status text,
                      source text,
                      published_at text
                    );
                    insert into youtube_videos values (1, ''), (2, '');
                    insert into pipeline_rows values
                      (1, 'scoped', 'Scoped', 'https://youtu.be/scoped',
                       'unreviewed', 'mapping_pending', 'Source', '2026-07-26'),
                      (2, 'legacy', 'Legacy', 'https://youtu.be/legacy',
                       'unreviewed', 'mapping_pending', 'Source', '2025-01-01');
                    create view video_pipeline_status as select * from pipeline_rows;
                    """
                )

            counts = backlog.process_backlog(
                sqlite_path,
                dry_run=True,
                enrich_missing_metadata=False,
                source="Source",
                video_ids=["scoped"],
            )

        self.assertEqual(counts["not_restaurant_or_uncertain"], 1)

    def test_resolver_loads_only_requested_video_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sqlite_path = Path(directory) / "test.sqlite"
            with sqlite3.connect(sqlite_path) as connection:
                connection.executescript(
                    """
                    create table sources (id integer primary key, name text);
                    create table youtube_videos (
                      id integer primary key,
                      source_id integer,
                      video_id text,
                      title text,
                      url text,
                      published_at text
                    );
                    create table place_resolution_candidates (
                      id integer primary key,
                      youtube_video_id integer,
                      status text,
                      query text,
                      result_name text,
                      result_address text,
                      result_phone text,
                      result_category text,
                      result_rank integer
                    );
                    insert into sources values (1, 'Source');
                    insert into youtube_videos values
                      (1, 1, 'scoped', 'Scoped', 'https://youtu.be/scoped', '2026-07-26'),
                      (2, 1, 'legacy', 'Legacy', 'https://youtu.be/legacy', '2025-01-01');
                    insert into place_resolution_candidates values
                      (1, 1, 'needs_review', 'Scoped', 'Scoped', '서울시 강남구', '', '', 1),
                      (2, 2, 'needs_review', 'Legacy', 'Legacy', '서울시 종로구', '', '', 1);
                    """
                )

            candidates = resolver.load_candidates(
                sqlite_path,
                "Source",
                missing_only=False,
                limit=None,
                video_ids=["scoped"],
            )

        self.assertEqual([candidate.video_id for candidate in candidates], ["scoped"])


if __name__ == "__main__":
    unittest.main()
