# Enterprise General Affair Management System

Sistem manajemen General Affair berbasis Django dengan workflow tracking dan integrasi WhatsApp broadcast via Fonnte API.

## Fitur Utama

- **Authentication & Role** — Custom User model dengan 3 role: Employee, GA, Manager
- **Pengajuan Service Request** — CRUD dengan kategori, urgensi, lampiran
- **Workflow Tracking** — Status: Pending → Verified → On Progress → Completed / Rejected
- **Audit Trail & Timeline** — Setiap perubahan status tercatat dengan timestamp dan user
- **Dashboard** — Employee & GA dashboard dengan statistik dan grafik (Chart.js)
- **WhatsApp Broadcast** — Notifikasi otomatis via Fonnte API menggunakan Django Signals
- **Dynamic Message Template** — Template pesan yang bisa dikustomisasi via admin
- **Notification Log** — Pencatatan setiap pengiriman WA (sent/failed)

---

## ERD (Entity Relationship Diagram)

```
┌──────────────────────────┐
│         User             │
├──────────────────────────┤
│ id          (PK)         │
│ username                 │
│ email                    │
│ first_name               │
│ last_name                │
│ password                 │
│ role        (employee/   │
│              ga/manager) │
│ phone                    │
│ is_active                │
└──────────┬───────────────┘
           │ 1
           │
           │ N
┌──────────▼───────────────┐        ┌─────────────────────────┐
│     ServiceRequest       │        │       RequestLog        │
├──────────────────────────┤        ├─────────────────────────┤
│ id          (PK)         │ 1    N │ id          (PK)        │
│ requester   (FK → User)  │───────►│ service_request (FK)    │
│ category                 │        │ old_status              │
│ description              │        │ new_status              │
│ location                 │        │ updated_by  (FK → User) │
│ urgency                  │        │ notes                   │
│ attachment               │        │ created_at              │
│ status                   │        └─────────────────────────┘
│ created_at               │
│ updated_at               │
└──────────┬───────────────┘
           │ 1
           │
           │ N
┌──────────▼───────────────┐
│    NotificationLog       │
├──────────────────────────┤
│ id          (PK)         │
│ service_request (FK)     │
│ recipient   (FK → User)  │
│ message                  │
│ status      (sent/failed)│
│ api_response             │
│ created_at               │
└──────────────────────────┘

┌──────────────────────────┐
│    MessageTemplate       │
├──────────────────────────┤
│ id          (PK)         │
│ code        (unique)     │
│ template_text            │
│ is_active                │
└──────────────────────────┘
```

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Backend     | Django 5.2              |
| Database    | PostgreSQL              |
| Frontend    | Bootstrap 5, Chart.js   |
| WhatsApp    | Fonnte API              |
| Env Config  | python-decouple         |

---

## Struktur Project

```
ga_system/
├── ga_system/          # Project settings & root URL
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/              # Custom User, auth, middleware
│   ├── models.py       # User(AbstractUser) + role + phone
│   ├── views.py        # Login, Logout, DashboardRedirect
│   ├── forms.py        # LoginForm
│   ├── services.py     # get_users_by_role, get_user_phone
│   ├── decorators.py   # role_required
│   ├── middleware.py    # RoleMiddleware
│   └── admin.py
├── requests_app/       # Service Request & Tracking
│   ├── models.py       # ServiceRequest, RequestLog
│   ├── views.py        # CRUD, Dashboards (Employee & GA)
│   ├── forms.py        # ServiceRequestForm, StatusUpdateForm
│   ├── services.py     # create_request, update_status
│   ├── signals.py      # WA triggers on create & status change
│   └── admin.py
├── notifications/      # WhatsApp integration
│   ├── models.py       # MessageTemplate, NotificationLog
│   ├── views.py        # NotificationLogListView
│   ├── services.py     # Fonnte API, template rendering
│   └── admin.py
├── templates/          # HTML templates (Bootstrap 5)
├── static/css/         # Custom styles
├── media/              # Uploaded attachments
├── .env.example        # Environment variables template
├── requirements.txt
└── manage.py
```

---

## Setup & Installation

### 1. Clone & Virtual Environment

```bash
cd ga_system
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
cp .env.example .env
# Edit .env dengan konfigurasi Anda
```

### 4. Database Setup

Pastikan PostgreSQL sudah running, lalu buat database:

```sql
CREATE DATABASE ga_system_db;
```

### 5. Migrations

```bash
python manage.py makemigrations users requests_app notifications
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Load Message Templates (Optional)

Melalui Django Admin (`/admin/`), tambahkan MessageTemplate:

| code               | template_text                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| request_created    | Halo GA, ada pengajuan baru dari {nama} kategori {kategori} di {lokasi}.      |
| request_completed  | Halo {nama}, pengajuan {kategori} telah selesai pada {tanggal}.               |
| request_rejected   | Halo {nama}, pengajuan {kategori} ditolak pada {tanggal}.                     |

### 8. Run Server

```bash
python manage.py runserver
```

Akses: [http://localhost:8000](http://localhost:8000)

---

## Environment Variables

| Variable        | Description                | Default       |
|-----------------|----------------------------|---------------|
| `SECRET_KEY`    | Django secret key          | insecure key  |
| `DEBUG`         | Debug mode                 | `True`        |
| `ALLOWED_HOSTS` | Comma-separated hosts      | `localhost`   |
| `DB_NAME`       | PostgreSQL database name   | `ga_system_db`|
| `DB_USER`       | PostgreSQL user            | `postgres`    |
| `DB_PASSWORD`   | PostgreSQL password        | (empty)       |
| `DB_HOST`       | PostgreSQL host            | `localhost`   |
| `DB_PORT`       | PostgreSQL port            | `5432`        |
| `FONNTE_TOKEN`  | Fonnte API token for WA    | (empty)       |

---

## Running Tests

```bash
python manage.py test users requests_app notifications --verbosity=2
```

---

## License

Internal Enterprise System — All rights reserved.
