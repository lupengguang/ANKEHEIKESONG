# -*- coding: utf-8 -*-
"""av_alarm 告警表 AI 升级：新增场景类型 / AI 分析 / 触发动作 / 截图字段。

采用 raw SQL（SQLite ALTER TABLE ADD COLUMN 支持 NOT NULL DEFAULT），
与 0003/0004 风格保持一致。
"""
from django.db import migrations


ADD_COLUMNS_SQL = [
    "ALTER TABLE av_alarm ADD COLUMN scene_type VARCHAR(50) NOT NULL DEFAULT ''",
    "ALTER TABLE av_alarm ADD COLUMN ai_description TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE av_alarm ADD COLUMN triggered_actions TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE av_alarm ADD COLUMN snapshot_path VARCHAR(255) NOT NULL DEFAULT ''",
]

DROP_COLUMNS_SQL = [
    "ALTER TABLE av_alarm DROP COLUMN scene_type",
    "ALTER TABLE av_alarm DROP COLUMN ai_description",
    "ALTER TABLE av_alarm DROP COLUMN triggered_actions",
    "ALTER TABLE av_alarm DROP COLUMN snapshot_path",
]


def add_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for sql in ADD_COLUMNS_SQL:
            cursor.execute(sql)


def drop_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for sql in DROP_COLUMNS_SQL:
            cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_seed_devices"),
    ]

    operations = [
        migrations.RunPython(add_columns, drop_columns),
    ]
