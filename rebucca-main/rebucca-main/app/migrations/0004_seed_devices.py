# -*- coding: utf-8 -*-
"""种子数据：3 台测试设备（幂等，可重复执行）。

说明：0003 采用 raw SQL 建表，迁移状态中未登记 Device 模型，
因此这里同样使用 raw SQL 写入，保持与 0003 一致。
"""
from django.db import migrations


SEED_DEVICES = [
    ("cam-001", "前门庭院4G摄像机", "4g", "192.168.1.101", "online", 85, "v1.2.0"),
    ("cam-002", "客厅室内摄像机", "indoor", "192.168.1.102", "online", -1, "v1.2.0"),
    ("cam-003", "户外NVR套装", "nvr", "192.168.1.103", "online", -1, "v1.0.4"),
]

INSERT_SQL = """
INSERT INTO devices
  (device_id, name, type, ip, status, battery, firmware, registered_at)
SELECT %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM devices WHERE device_id = %s)
"""

DELETE_SQL = "DELETE FROM devices WHERE device_id = %s"


def seed_devices(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for row in SEED_DEVICES:
            cursor.execute(INSERT_SQL, list(row) + [row[0]])


def unseed_devices(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for row in SEED_DEVICES:
            cursor.execute(DELETE_SQL, [row[0]])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0003_indoor_offline_devices"),
    ]

    operations = [
        migrations.RunPython(seed_devices, unseed_devices),
    ]
