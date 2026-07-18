"""Create forecast_runs table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("latest_close", sa.Float(), nullable=False),
        sa.Column("predicted_return_percent", sa.Float(), nullable=False),
        sa.Column("predicted_price", sa.Float(), nullable=False),
        sa.Column("price_range_low", sa.Float(), nullable=False),
        sa.Column("price_range_high", sa.Float(), nullable=False),
        sa.Column("probability_up_percent", sa.Float(), nullable=False),
        sa.Column("training_observations", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("model_version", sa.String(120), nullable=False),
        sa.Column("model_mae_percent", sa.Float(), nullable=False),
        sa.Column("baseline_mae_percent", sa.Float(), nullable=False),
        sa.Column("directional_accuracy_percent", sa.Float(), nullable=False),
        sa.Column("validation_observations", sa.Integer(), nullable=False),
        sa.Column("beats_baseline", sa.Boolean(), nullable=False),
        sa.Column("signal_status", sa.String(20), nullable=False),
        sa.Column(
            "trained_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_forecast_runs_symbol", "forecast_runs", ["symbol"])
    op.create_index("ix_forecast_runs_symbol_trained", "forecast_runs", ["symbol", "trained_at"])


def downgrade() -> None:
    op.drop_index("ix_forecast_runs_symbol_trained", table_name="forecast_runs")
    op.drop_index("ix_forecast_runs_symbol", table_name="forecast_runs")
    op.drop_table("forecast_runs")
