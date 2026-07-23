"""Add sentiment and model comparison fields to forecast_runs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("forecast_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sentiment_features_used",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "model_comparison_json",
                sa.Text(),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("forecast_runs") as batch_op:
        batch_op.drop_column("model_comparison_json")
        batch_op.drop_column("sentiment_features_used")
