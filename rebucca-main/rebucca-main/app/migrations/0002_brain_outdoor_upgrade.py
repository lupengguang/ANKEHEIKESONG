"""手动创建脑中枢和户外场景的 5 张新表。

原因：0001_initial 迁移早在 Agent 追加新模型之前就已经被标记为 applied，
后续 regenerate 0001_initial.py 不会触发新的 migration。
本文件作为 0002 号迁移，用 raw SQL 补建缺失表。
"""
from django.db import migrations, models


SQL_CREATE_BRAIN_EVENT = """
CREATE TABLE IF NOT EXISTS brain_event (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id       INTEGER NOT NULL,
    timestamp       DATETIME NOT NULL,
    event_type      VARCHAR(50) NOT NULL DEFAULT 'motion',
    scene_description TEXT NOT NULL DEFAULT '',
    subject         VARCHAR(100) NOT NULL DEFAULT '',
    action          VARCHAR(200) NOT NULL DEFAULT '',
    anomaly_score   REAL NOT NULL DEFAULT 0.0,
    snapshot_path   VARCHAR(500) NOT NULL DEFAULT '',
    video_clip_path VARCHAR(500) NOT NULL DEFAULT '',
    create_time     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS be_cam_ts_idx ON brain_event (camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS be_ts_idx     ON brain_event (timestamp DESC);
"""

SQL_CREATE_BEHAVIOR_TRACK = """
CREATE TABLE IF NOT EXISTS brain_behavior_track (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id          VARCHAR(100) NOT NULL,
    camera_sequence   TEXT NOT NULL DEFAULT '[]',
    start_time        DATETIME NOT NULL,
    end_time          DATETIME NOT NULL,
    total_duration    REAL NOT NULL DEFAULT 0.0,
    create_time       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS bt_track_idx ON brain_behavior_track (track_id);
"""

SQL_CREATE_WEEKLY_REPORT = """
CREATE TABLE IF NOT EXISTS brain_weekly_report (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start      DATE NOT NULL,
    week_end        DATE NOT NULL,
    summary         TEXT NOT NULL DEFAULT '',
    anomaly_count   INTEGER NOT NULL DEFAULT 0,
    report_content  TEXT NOT NULL DEFAULT '',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_OUTDOOR_SCENE_CONFIG = """
CREATE TABLE IF NOT EXISTS outdoor_scene_config (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id       INTEGER NOT NULL,
    scene_type      VARCHAR(50) NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 1,
    config          TEXT NOT NULL DEFAULT '{}',
    create_time     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS osc_cam_idx ON outdoor_scene_config (camera_id);
"""

SQL_CREATE_OUTDOOR_EVENT = """
CREATE TABLE IF NOT EXISTS outdoor_event (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id         INTEGER NOT NULL,
    event_type        VARCHAR(50) NOT NULL,
    person_type       VARCHAR(20) NOT NULL DEFAULT 'unknown',
    person_confidence REAL NOT NULL DEFAULT 0.0,
    timestamp         DATETIME NOT NULL,
    snapshot_path     VARCHAR(500) NOT NULL DEFAULT '',
    actions_taken     TEXT NOT NULL DEFAULT '[]',
    notified          INTEGER NOT NULL DEFAULT 0,
    create_time       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS oe_cam_ts_idx ON outdoor_event (camera_id, timestamp DESC);
"""


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL_CREATE_BRAIN_EVENT, "DROP TABLE IF EXISTS brain_event"),
        migrations.RunSQL(SQL_CREATE_BEHAVIOR_TRACK, "DROP TABLE IF EXISTS brain_behavior_track"),
        migrations.RunSQL(SQL_CREATE_WEEKLY_REPORT, "DROP TABLE IF EXISTS brain_weekly_report"),
        migrations.RunSQL(SQL_CREATE_OUTDOOR_SCENE_CONFIG, "DROP TABLE IF EXISTS outdoor_scene_config"),
        migrations.RunSQL(SQL_CREATE_OUTDOOR_EVENT, "DROP TABLE IF EXISTS outdoor_event"),
    ]
