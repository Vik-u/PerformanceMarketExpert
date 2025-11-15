from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from adpulse.api.dependencies import get_db
from adpulse.api.main import app
from adpulse.database import Base
from adpulse.models import AdPerformance


def test_platform_summary_endpoint(tmp_path):
    test_db = tmp_path / "api_test.db"
    engine = create_engine(f"sqlite:///{test_db}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        session.add_all(
            [
                AdPerformance(
                    platform="Google Ads",
                    campaign_id="google-brand",
                    campaign_name="Brand",
                    event_date=date(2024, 5, 1).isoformat(),
                    impressions=1000,
                    clicks=100,
                    spend=200.0,
                    conversions=10,
                    revenue=500.0,
                ),
                AdPerformance(
                    platform="Meta Ads",
                    campaign_id="meta-brand",
                    campaign_name="Brand",
                    event_date=date(2024, 5, 1).isoformat(),
                    impressions=500,
                    clicks=50,
                    spend=150.0,
                    conversions=5,
                    revenue=250.0,
                ),
            ]
        )
        session.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    response = client.get("/summary/platforms")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    google_metrics = next(item for item in payload if item["platform"] == "Google Ads")
    assert google_metrics["total_spend"] == 200.0
    assert google_metrics["total_clicks"] == 100
    assert google_metrics["ctr"] == 0.1
    assert google_metrics["roas"] == 2.5

    app.dependency_overrides.clear()
