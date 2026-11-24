from sqlalchemy import Column, Index, Integer, String, Text

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    metadata_json = Column("metadata", Text, nullable=True)  # JSON string, assistant only
    created_at = Column(String, nullable=False)  # ISO-8601, server time

    __table_args__ = (Index("ix_messages_session_id", "session_id"),)
