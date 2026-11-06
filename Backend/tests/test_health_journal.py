from datetime import datetime, timedelta, timezone

from app.api import health_journal
from app.database.connection import SessionLocal
from app.models.health_journal import HealthReminder


BASE = "/api/v1/health-journal"


def test_measurements_are_validated_and_account_scoped(client, auth, other_auth):
    response = client.post(
        f"{BASE}/measurements",
        headers=auth,
        json={
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "weight_kg": 68.5,
        },
    )
    assert response.status_code == 201
    assert response.json()["measured_at"].endswith("Z")
    measurement_id = response.json()["id"]
    assert client.get(f"{BASE}/measurements", headers=auth).json()[0]["weight_kg"] == 68.5
    assert client.get(f"{BASE}/measurements", headers=other_auth).json() == []
    assert client.delete(f"{BASE}/measurements/{measurement_id}", headers=other_auth).status_code == 404

    invalid = client.post(
        f"{BASE}/measurements",
        headers=auth,
        json={"measured_at": datetime.now(timezone.utc).isoformat(), "systolic_bp": 120},
    )
    assert invalid.status_code == 422


def test_visit_preparation_is_account_scoped(client, auth, other_auth):
    data = {
        "symptoms": "Occasional dizziness",
        "medications": "Medicine A, 5 mg",
        "questions": "Should I monitor this?",
        "bring_medications": True,
        "bring_test_results": False,
    }
    assert client.put(f"{BASE}/visit-preparation", headers=auth, json=data).status_code == 200
    assert client.get(f"{BASE}/visit-preparation", headers=auth).json()["symptoms"] == data["symptoms"]
    assert client.get(f"{BASE}/visit-preparation", headers=other_auth).json()["symptoms"] == ""


def test_reminders_require_explicit_opt_in_and_are_account_scoped(client, auth, other_auth, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "reminders@example.test")
    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {"kind": "screening", "scheduled_at": scheduled_at, "note": "Check in"}

    assert client.get(f"{BASE}/reminder-preferences", headers=auth).json()["email_enabled"] is False
    assert client.post(f"{BASE}/reminders", headers=auth, json=payload).status_code == 409
    assert client.put(f"{BASE}/reminder-preferences", headers=auth, json={"email_enabled": True}).json()["email_enabled"]

    response = client.post(f"{BASE}/reminders", headers=auth, json=payload)
    assert response.status_code == 201
    reminder_id = response.json()["id"]
    assert response.json()["scheduled_at"].endswith("Z")
    assert client.get(f"{BASE}/reminders", headers=other_auth).json() == []
    assert client.patch(f"{BASE}/reminders/{reminder_id}", headers=other_auth, json={"enabled": False}).status_code == 404
    opted_out = client.put(f"{BASE}/reminder-preferences", headers=auth, json={"email_enabled": False})
    assert opted_out.json()["email_enabled"] is False
    assert client.get(f"{BASE}/reminders", headers=auth).json()[0]["enabled"] is False


def test_dispatch_authenticates_and_sends_due_generic_reminder(client, auth, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "reminders@example.test")
    monkeypatch.setenv("REMINDER_JOB_TOKEN", "scheduler-test-token")
    client.put(f"{BASE}/reminder-preferences", headers=auth, json={"email_enabled": True})
    created = client.post(
        f"{BASE}/reminders",
        headers=auth,
        json={"kind": "referral", "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
    )
    assert created.status_code == 201
    reminder_id = created.json()["id"]
    db = SessionLocal()
    try:
        db.query(HealthReminder).filter(HealthReminder.id == reminder_id).update(
            {HealthReminder.scheduled_at: datetime.now(timezone.utc) - timedelta(minutes=1)}
        )
        db.commit()
    finally:
        db.close()

    sent = []
    monkeypatch.setattr(health_journal, "send_reminder_email", lambda *args: sent.append(args))
    url = f"{BASE}/reminders/dispatch"
    assert client.post(url).status_code == 401
    headers = {"Authorization": "Bearer scheduler-test-token"}
    assert client.post(url, headers=headers).json() == {"sent": 1}
    assert len(sent) == 1 and sent[0][1] == "referral"
    assert client.post(url, headers=headers).json() == {"sent": 0}
