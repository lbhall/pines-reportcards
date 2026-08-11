# Pines Report Cards

Django app that generates middle-school report cards for Pines Montessori School.
Teachers enter assessments, designations (Dsgn), work habits, and attendance per
grading period; the app renders a print-ready report card page matching the
school's document layout (US Letter landscape — use the browser's Print to save
as PDF).

## Features

- **Students** — name and date of birth
- **Subjects** — editable core subjects and resources (pass/fail classes), with
  ordering and an active flag
- **School years** — label, two faculty signature lines, and editable grading
  periods (Quarter 0–4) with date ranges
- **Report card entry** — grid of subjects × quarters; each cell takes a
  free-form assessment ("83%", "P", "INC", "N/A"), a Designation dropdown
  (L / A / L/M / M) and a Work Habits dropdown (Mastered / Competent /
  Improving / Reminders Needed); plus absences and tardies per quarter
- **Printable report card** — reproduces the school document, including the
  legend footnotes and signature lines
- Login required throughout (Django auth); user management via `/admin`

## Development

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_defaults   # default subjects + 2025-26 year
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Tests and lint (CI enforces both, coverage must stay ≥ 80%):

```bash
.venv/bin/coverage run manage.py test && .venv/bin/coverage report
.venv/bin/ruff check .
```

## Deployment

Merges to `main` deploy automatically via GitHub Actions (`ci.yml`): lint +
tests, then SSH to the server and run `deploy.sh`, which pulls, installs,
migrates, collects static files, and restarts `gunicorn.reportcards.service`.

Environment (in `/etc/gunicorn.reportcards.env`, loaded by the systemd unit):
`SECRET_KEY`, `DEBUG=false`, `ALLOWED_HOSTS`, and `DJANGO_DB_PATH` pointing at
the sqlite file **outside the checkout** (`../data/db.sqlite3`) so git
operations can never touch it.

### Backups

`backup.sh` makes a consistent online backup of the sqlite database (safe
while the app is running), gzips it into `../backups/db-YYYY-MM-DD.sqlite3.gz`,
and prunes anything older than 30 days. Install as a nightly cron job:

```
15 2 * * * bash /var/www/reportcards.emcfunleague.com/source/backup.sh
```

Restore: `gunzip` the chosen backup, stop the service, replace the file at
`DJANGO_DB_PATH`, start the service.

### One-time server setup

1. nginx vhost for `reportcards.emcfunleague.com`; site root
   `/var/www/reportcards.emcfunleague.com/source` (git checkout) with venv at
   `../venv`
2. systemd unit `gunicorn.reportcards` running
   `gunicorn pines.wsgi:application`
3. sudoers rule (must match deploy.sh's restart command exactly):
   `bhall ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart gunicorn.reportcards.service`
4. Repo secret `DEPLOY_SSH_KEY` with the deploy private key
