import re
import sqlite3
import time
from pathlib import Path

MEDIA_NAME = re.compile(r"[a-f0-9]{32}\.(?:jpg|mp4)\Z")


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        self.media = directory / "media"
        self.media.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(directory / "reef.sqlite3", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY, at REAL NOT NULL, kind TEXT, title TEXT, detail TEXT,
                snapshot TEXT, clip TEXT, acknowledged INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY, at REAL NOT NULL, day TEXT NOT NULL, file TEXT NOT NULL,
                automatic INTEGER NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS daily_snapshot ON snapshots(day) WHERE automatic=1;
            CREATE TABLE IF NOT EXISTS metrics (at REAL, brightness REAL, motion REAL, phase TEXT);
            CREATE INDEX IF NOT EXISTS metric_time ON metrics(at);
        """)

    def event(self, event_id, observation, at, snapshot=None):
        self.db.execute(
            "INSERT INTO events(id,at,kind,title,detail,snapshot) VALUES(?,?,?,?,?,?)",
            (event_id, at, observation.kind, observation.title, observation.detail, snapshot),
        )
        self.db.commit()

    def events(self):
        return [
            dict(row) for row in self.db.execute("SELECT * FROM events ORDER BY at DESC LIMIT 100")
        ]

    def attach_clip(self, event_id, clip):
        self.db.execute("UPDATE events SET clip=? WHERE id=?", (clip, event_id))
        self.db.commit()

    def acknowledge(self, event_id):
        cursor = self.db.execute("UPDATE events SET acknowledged=1 WHERE id=?", (event_id,))
        self.db.commit()
        return bool(cursor.rowcount)

    def snapshot(self, item_id, at, day, filename, automatic):
        self.db.execute(
            "INSERT INTO snapshots VALUES(?,?,?,?,?)", (item_id, at, day, filename, int(automatic))
        )
        self.db.commit()

    def snapshots(self):
        return [
            dict(row)
            for row in self.db.execute("SELECT * FROM snapshots ORDER BY at DESC LIMIT 30")
        ]

    def has_daily(self, day):
        return (
            self.db.execute(
                "SELECT 1 FROM snapshots WHERE day=? AND automatic=1", (day,)
            ).fetchone()
            is not None
        )

    def metric(self, at, values):
        self.db.execute(
            "INSERT INTO metrics VALUES(?,?,?,?)",
            (at, values["brightness"], values["motion"], values["phase"]),
        )
        self.db.commit()

    def prune(self, days, now=None):
        cutoff = (time.time() if now is None else now) - days * 86400
        for table in ("events", "snapshots", "metrics"):
            self.db.execute(f"DELETE FROM {table} WHERE at < ?", (cutoff,))
        self.db.commit()
        referenced = {
            row[0]
            for row in self.db.execute(
                "SELECT snapshot FROM events UNION SELECT clip FROM events UNION SELECT file FROM snapshots"
            )
        }
        for path in self.media.iterdir():
            if (
                MEDIA_NAME.fullmatch(path.name)
                and path.name not in referenced
                and path.stat().st_mtime < cutoff
            ):
                path.unlink()

    def close(self):
        self.db.close()
