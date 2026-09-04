import uuid
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.services.evaluation_service import EvaluationService


@pytest.mark.asyncio
async def test_50_record_evaluation_batch(session: AsyncSession):
    # Setup workspace
    user_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    ws = Workspace(
        id=ws_id,
        name="Buildathon Test Merchant",
        kind="business",
        default_currency="INR",
    )
    session.add(ws)
    await session.commit()

    # Run 50+ record evaluation loop
    batch = await EvaluationService.run_full_demo_loop(
        session=session,
        workspace_id=ws_id,
        total_records=60,
    )

    assert batch.total_records == 60
    assert batch.status == "completed"
    assert batch.duration_ms >= 0
    assert batch.throughput_rps > Decimal("0.00")

    # Match rate must be dynamically measured (expected ~80-95%)
    assert Decimal("0.7000") <= batch.match_rate <= Decimal("0.9800")
    assert batch.auto_reconciled > 0

    # Exceptions must be explicitly reported (never zero when anomalies injected)
    assert batch.unresolved_count > 0
    assert batch.financial_exposure > Decimal("0.00")
    assert batch.ai_assisted > 0
