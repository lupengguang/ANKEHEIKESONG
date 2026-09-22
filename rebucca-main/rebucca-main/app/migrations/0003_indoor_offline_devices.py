# -*- coding: utf-8 -*-
"""手动创建室内互动 / 无网场景 / 设备联动中枢的 6 张新表。

沿用 0002 的 raw SQL 方式（0001 已标记 applied，新模型只能通过新迁移补建）。
列名与 app/models.py 中的模型字段严格一致，避免 ORM 读写错位。
"""
from django.db import migrations


SQL_CREATE_INDOOR_SCENE_CONFIG = """
CREATE TABLE IF NOT EXISTS indoor_scene_config (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id        INTEGER NOT NULL,
    scene_type       VARCHAR(50) NOT NULL DEFAULT 'general',
    enabled          INTEGER NOT NULL DEFAULT 1,
    config           TEXT NOT NULL DEFAULT '{}',
    create_time      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS isc_cam_idx ON indoor_scene_config (camera_id);
"""

SQL_CREATE_INDOOR_EVENTS = """
CREATE TABLE IF NOT EXISTS indoor_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id      INTEGER NOT NULL,
    event_type     VARCHAR(50) NOT NULL,
    scene_mode     VARCHAR(50) NOT NULL DEFAULT '',
    timestamp      DATETIME NOT NULL,
    snapshot_path  VARCHAR(500) NOT NULL DEFAULT '',
    actions_taken  TEXT NOT NULL DEFAULT '[]',
    notified       INTEGER NOT NULL DEFAULT 0,
    create_time    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ie_cam_ts_idx ON indoor_events (camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ie2_ts_idx    ON indoor_events (timestamp DESC);
"""

SQL_CREATE_OFFLINE_SCENE_CONFIG = """
CREATE TABLE IF NOT EXISTS offline_scene_config (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id        INTEGER NOT NULL,
    enabled          INTEGER NOT NULL DEFAULT 1,
    config           TEXT NOT NULL DEFAULT '{}',
    create_time      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ofsc_cam_idx ON offline_scene_config (camera_id);
"""

SQL_CREATE_OFFLINE_EVENTS = """
CREATE TABLE IF NOT EXISTS offline_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id      INTEGER NOT NULL,
    event_type     VARCHAR(50) NOT NULL,
    timestamp      DATETIME NOT NULL,
    snapshot_path  VARCHAR(500) NOT NULL DEFAULT '',
    video_path     VARCHAR(500) NOT NULL DEFAULT '',
    is_replayed    INTEGER NOT NULL DEFAULT 0,
    replayed_at    DATETIME NULL,
    create_time    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ofe_cam_ts_idx ON offline_events (camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ofe_ts_idx     ON offline_events (timestamp DESC);
"""

SQL_CREATE_DEVICES = """
CREATE TABLE IF NOT EXISTS devices (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id      VARCHAR(80) NOT NULL UNIQUE,
    name           VARCHAR(100) NOT NULL DEFAULT '',
    type           VARCHAR(20) NOT NULL DEFAULT 'outdoor',
    ip             VARCHAR(50) NOT NULL DEFAULT '',
    status         VARCHAR(20) NOT NULL DEFAULT 'offline',
    battery        INTEGER NOT NULL DEFAULT -1,
    firmware       VARCHAR(50) NOT NULL DEFAULT '',
    registered_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS dev_status_idx ON devices (status);
"""

SQL_CREATE_DEVICE_COMMANDS = """
CREATE TABLE IF NOT EXISTS device_commands (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id     INTEGER NULL REFERENCES devices(id) ON DELETE SET NULL,
    command_type  VARCHAR(30) NOT NULL,
    payload       TEXT NOT NULL DEFAULT '{}',
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed_at   DATETIME NULL
);
CREATE INDEX IF NOT EXISTS dc_created_idx ON device_commands (created_at DESC);
CREATE INDEX IF NOT EXISTS dc_status_idx  ON device_commands (status);
"""


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_brain_outdoor_upgrade"),
    ]

    operations = [
        migrations.RunSQL(SQL_CREATE_INDOOR_SCENE_CONFIG,
                          "DROP TABLE IF EXISTS indoor_scene_config"),
        migrations.RunSQL(SQL_CREATE_INDOOR_EVENTS,
                          "DROP TABLE IF EXISTS indoor_events"),
        migrations.RunSQL(SQL_CREATE_OFFLINE_SCENE_CONFIG,
                          "DROP TABLE IF EXISTS offline_scene_config"),
        migrations.RunSQL(SQL_CREATE_OFFLINE_EVENTS,
                          "DROP TABLE IF EXISTS offline_events"),
        migrations.RunSQL(SQL_CREATE_DEVICES,
                          "DROP TABLE IF EXISTS devices"),
        migrations.RunSQL(SQL_CREATE_DEVICE_COMMANDS,
                          "DROP TABLE IF EXISTS device_commands"),
    ]
