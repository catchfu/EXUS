from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base, engine
import time

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)

class CNFT(Base):
    __tablename__ = 'cnfts'
    token_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner: Mapped[str] = mapped_column(String(120), index=True)
    commitment: Mapped[str] = mapped_column(String(128))
    nullifier: Mapped[str] = mapped_column(String(128))
    minted_at: Mapped[int] = mapped_column(Integer)
    cognitive_score: Mapped[float] = mapped_column(Float)
    total_earnings: Mapped[float] = mapped_column(Float)
    metadata_uri: Mapped[str] = mapped_column(String(256))

class Block(Base):
    __tablename__ = 'blocks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index: Mapped[int] = mapped_column(Integer, index=True)
    timestamp: Mapped[int] = mapped_column(Integer)
    hash: Mapped[str] = mapped_column(String(128), index=True)
    miner: Mapped[str] = mapped_column(String(120))
    transactions: Mapped[str] = mapped_column(Text)

class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()))
    updated_at: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()))
    result: Mapped[str] = mapped_column(Text, default='')

class OAuthToken(Base):
    __tablename__ = 'oauth_tokens'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    token_encrypted: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()))

Base.metadata.create_all(bind=engine)

