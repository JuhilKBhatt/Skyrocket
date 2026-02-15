from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from app.core.database import Base

class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    sentiment_score = Column(Float, nullable=False)  # The probability (e.g. 0.95)
    sentiment_label = Column(String, nullable=False) # "positive", "negative", "neutral"

    # Ensure we don't save duplicate sentiment for the same symbol on the same day
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_symbol_date'),
    )