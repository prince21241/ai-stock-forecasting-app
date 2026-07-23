"""Add calibration, sentiment comparison, and multi-horizon forecast fields."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("forecast_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sentiment_comparison_json",
                sa.Text(),
                nullable=False,
                server_default="{}",
            )
        )
        batch_op.add_column(
            sa.Column(
                "calibration_json",
                sa.Text(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "horizons_json",
                sa.Text(),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("forecast_runs") as batch_op:
        batch_op.drop_column("horizons_json")
        batch_op.drop_column("calibration_json")
        batch_op.drop_column("sentiment_comparison_json")
