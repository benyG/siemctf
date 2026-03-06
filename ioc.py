from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, Boolean, DateTime, Float, ForeignKey
from app.core.db import Base

class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    parsed_records: Mapped[int] = mapped_column(Integer, default=0)
    partial_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)

class RawRecord(Base):
    __tablename__ = "raw_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    source_file: Mapped[str] = mapped_column(String(255))
    line_number: Mapped[int] = mapped_column(Integer)
    raw_text: Mapped[str] = mapped_column(Text)
    detected_format: Mapped[str] = mapped_column(String(50), default="unknown")
    parser_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    raw_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(100), index=True, default="unknown")
    event_type: Mapped[str] = mapped_column(String(100), index=True, default="generic_event")
    hostname: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    src_ip: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    command_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(30), default="info")
    message: Mapped[str] = mapped_column(Text, default="")
    parse_status: Mapped[str] = mapped_column(String(20), default="parsed")
    parse_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    parser_name: Mapped[str] = mapped_column(String(100), default="unknown")
    ioc_match: Mapped[str | None] = mapped_column(String(255), nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    rule_id: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(30), default="medium")
    status: Mapped[str] = mapped_column(String(30), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    hostname: Mapped[str] = mapped_column(String(120), index=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    criticality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)

class IOC(Base):
    __tablename__ = "iocs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    type: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(255), index=True)
    threat_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)

class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    flag: Mapped[str] = mapped_column(String(255))
    location_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_value: Mapped[str | None] = mapped_column(Text, nullable=True)
