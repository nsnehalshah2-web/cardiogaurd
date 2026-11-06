import uuid

from app import screening_model

HEALTHY = dict(age=35, sex=0, smoker=0, cigs_per_day=0, bp_medication=0, prior_stroke=0,
               hypertension=0, diabetes=0, systolic_bp=112, bmi=21.5)
AT_RISK = dict(age=64, sex=1, smoker=1, cigs_per_day=20, bp_medication=1, prior_stroke=0,
               hypertension=1, diabetes=1, systolic_bp=168, bmi=29)


def cid():
    return uuid.uuid4().hex


def test_public_model_matches_server_prediction(client):
    model = client.get("/api/v1/screening/model").json()
    assert model["features"] == screening_model.MODEL["features"]
    assert "fairness" not in model  # only parameters are public


def test_risk_ordering_and_bands(client, auth):
    low = client.post("/api/v1/screening/predict?persist=false", json=HEALTHY, headers=auth).json()
    high = client.post("/api/v1/screening/predict?persist=false", json=AT_RISK, headers=auth).json()
    assert low["risk_probability"] < 10 and low["risk_category"] == "LOW"
    assert high["risk_probability"] >= 20 and high["risk_category"] == "HIGH"
    assert any(item["title"] == "Stop smoking" for item in high["recommendations"])


def test_unknown_bmi_is_accepted(client, auth):
    response = client.post("/api/v1/screening/predict?persist=false", json={**HEALTHY, "bmi": None}, headers=auth)
    assert response.status_code == 200


def test_invalid_input_rejected(client, auth):
    assert client.post("/api/v1/screening/predict", json={**HEALTHY, "systolic_bp": 20}, headers=auth).status_code == 422


def test_self_screening_history(client, auth):
    client.post("/api/v1/screening/predict", json=HEALTHY, headers=auth)
    history = client.get("/api/v1/screening/history", headers=auth).json()
    assert len(history) == 1 and history[0]["form_data"]["systolic_bp"] == 112


def test_sync_is_idempotent_and_recalculates_risk(client, auth):
    patient = {"client_id": cid(), "name": "Sunita Devi", "age": 64, "sex": 1, "village": "Rampur"}
    screening = {**AT_RISK, "client_id": cid(), "patient_client_id": patient["client_id"]}
    batch = {"patients": [patient], "screenings": [screening]}
    assert client.post("/api/v1/community/sync", json=batch, headers=auth).json() == {"rejected": []}
    client.post("/api/v1/community/sync", json=batch, headers=auth)  # resent after a dropped connection

    patients = client.get("/api/v1/community/patients", headers=auth).json()
    assert len(patients) == 1 and patients[0]["screening_count"] == 1
    assert patients[0]["latest"]["risk_category"] == "HIGH"


def test_referral_workflow(client, auth):
    patient = {"client_id": cid(), "name": "Ramesh"}
    screening = {**AT_RISK, "client_id": cid(), "patient_client_id": patient["client_id"]}
    client.post("/api/v1/community/sync", json={"patients": [patient], "screenings": [screening]}, headers=auth)
    patient_id = client.get("/api/v1/community/patients", headers=auth).json()[0]["id"]
    detail = client.get(f"/api/v1/community/patients/{patient_id}", headers=auth).json()
    screening_id = detail["screenings"][0]["id"]
    updated = client.patch(f"/api/v1/community/screenings/{screening_id}", json={"referral_status": "referred"}, headers=auth)
    assert updated.json()["referral_status"] == "referred"


def test_workers_cannot_see_each_others_patients(client, auth, other_auth):
    patient = {"client_id": cid(), "name": "Private Patient"}
    screening = {**HEALTHY, "client_id": cid(), "patient_client_id": patient["client_id"]}
    client.post("/api/v1/community/sync", json={"patients": [patient], "screenings": [screening]}, headers=auth)
    patient_id = client.get("/api/v1/community/patients", headers=auth).json()[0]["id"]
    screening_id = client.get(f"/api/v1/community/patients/{patient_id}", headers=auth).json()["screenings"][0]["id"]

    assert client.get("/api/v1/community/patients", headers=other_auth).json() == []
    assert client.get(f"/api/v1/community/patients/{patient_id}", headers=other_auth).status_code == 404
    assert client.patch(f"/api/v1/community/screenings/{screening_id}", json={"referral_status": "visited"},
                        headers=other_auth).status_code == 404
    # Reusing another worker's patient client_id is rejected, not merged.
    hijack = client.post("/api/v1/community/sync", json={"patients": [{**patient, "name": "Changed"}]}, headers=other_auth)
    assert hijack.json()["rejected"] == [patient["client_id"]]


def test_clinical_model_still_works(client, auth):
    data = dict(age=50, sex=1, cp=4, trestbps=120, chol=200, fbs=0, restecg=0, thalach=160, exang=0, oldpeak=0.0)
    response = client.post("/api/v1/predict?persist=false", json=data, headers=auth)
    assert response.status_code == 200
    insights = client.get("/api/v1/model-insights", headers=auth).json()
    assert {"calibration", "fairness"} <= set(insights)
