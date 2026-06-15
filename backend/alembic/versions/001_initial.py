"""Initial Phase 1 schema

Revision ID: 001
Revises:
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("asset_type", sa.String(50), nullable=True),
        sa.Column("exchange", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("first_traded", sa.Date(), nullable=True),
        sa.Column("last_traded", sa.Date(), nullable=True),
        sa.Column("provider_mappings", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index(op.f("ix_tickers_ticker"), "tickers", ["ticker"])

    op.create_table(
        "price_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timestamp_et", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session", sa.String(20), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("trade_count", sa.Integer(), nullable=True),
        sa.Column("bid", sa.Float(), nullable=True),
        sa.Column("ask", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_adjusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_price_bars_ticker_id"), "price_bars", ["ticker_id"])
    op.create_index(op.f("ix_price_bars_timestamp_utc"), "price_bars", ["timestamp_utc"])
    op.execute("SELECT create_hypertable('price_bars', 'timestamp_utc', if_not_exists => TRUE)")

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=True),
        sa.Column("provider_id", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tickers", postgresql.ARRAY(sa.String(20)), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_id", name="uq_news_provider_ref"),
    )
    op.create_index(op.f("ix_news_articles_ticker_id"), "news_articles", ["ticker_id"])
    op.create_index(op.f("ix_news_articles_published_utc"), "news_articles", ["published_utc"])

    op.create_table(
        "scored_news",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("news_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=False, unique=True),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("event_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("final_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("components", postgresql.JSONB(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("label", sa.String(50), nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("strategy_type", sa.String(100), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("strength", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("data_sources", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signals_ticker_id"), "signals", ["ticker_id"])
    op.create_index(op.f("ix_signals_generated_at"), "signals", ["generated_at"])

    op.create_table(
        "data_health",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="healthy"),
        sa.Column("warning_type", sa.String(100), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_health_ticker_id"), "data_health", ["ticker_id"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False, unique=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("watchlist_items")
    op.drop_table("data_health")
    op.drop_table("signals")
    op.drop_table("scored_news")
    op.drop_table("news_articles")
    op.drop_table("price_bars")
    op.drop_table("tickers")
