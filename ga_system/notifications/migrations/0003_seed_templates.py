"""
Data migration: seed MessageTemplate entries for all notification events.
Uses get_or_create to avoid duplicating templates that may already exist.
"""

from django.db import migrations


TEMPLATES = [
    {
        "code": "request_created",
        "template_text": (
            "📋 *Pengajuan Baru*\n"
            "Dari: {nama}\n"
            "Kategori: {kategori}\n"
            "Lokasi: {lokasi}\n"
            "Deskripsi: {deskripsi}\n"
            "Tanggal: {tanggal}\n\n"
            "Silakan cek di sistem GA untuk memproses."
        ),
    },
    {
        "code": "request_verified",
        "template_text": (
            "✅ *Pengajuan Diverifikasi*\n"
            "Halo {nama}, pengajuan {kategori} di {lokasi} "
            "telah diverifikasi oleh GA.\n"
            "Status: {status}\n"
            "Tanggal: {tanggal}"
        ),
    },
    {
        "code": "request_on_progress",
        "template_text": (
            "🔄 *Pengajuan Sedang Diproses*\n"
            "Halo {nama}, pengajuan {kategori} di {lokasi} "
            "sedang dalam proses pengerjaan.\n"
            "Status: {status}\n"
            "Tanggal: {tanggal}"
        ),
    },
    {
        "code": "request_completed",
        "template_text": (
            "🎉 *Pengajuan Selesai*\n"
            "Halo {nama}, pengajuan {kategori} di {lokasi} "
            "telah selesai dikerjakan.\n"
            "Status: {status}\n"
            "Tanggal: {tanggal}"
        ),
    },
    {
        "code": "request_rejected",
        "template_text": (
            "❌ *Pengajuan Ditolak*\n"
            "Halo {nama}, pengajuan {kategori} di {lokasi} "
            "telah ditolak.\n"
            "Status: {status}\n"
            "Tanggal: {tanggal}"
        ),
    },
    {
        "code": "manager_fyi",
        "template_text": (
            "📢 *Info Manager*\n"
            "Pengajuan #{request_id} ({kategori}) dari {nama}\n"
            "Status berubah menjadi: {status}\n"
            "Lokasi: {lokasi}\n"
            "Tanggal: {tanggal}"
        ),
    },
]


def seed_templates(apps, schema_editor):
    MessageTemplate = apps.get_model("notifications", "MessageTemplate")
    for tpl in TEMPLATES:
        MessageTemplate.objects.get_or_create(
            code=tpl["code"],
            defaults={"template_text": tpl["template_text"], "is_active": True},
        )


def remove_templates(apps, schema_editor):
    MessageTemplate = apps.get_model("notifications", "MessageTemplate")
    codes = [tpl["code"] for tpl in TEMPLATES]
    MessageTemplate.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(seed_templates, remove_templates),
    ]
