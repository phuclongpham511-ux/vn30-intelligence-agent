"""Materiality Engine V0: provisional deterministic backend baseline."""

from .models import EvidenceItem, EventDirection, EventType, MaterialEventCandidate, MaterialityCategory, MaterialityComponents, MaterialityResult
from .detectors import ScoringContext, detect_market_events, detect_fundamental_events
from .service import evaluate_candidate, detect_and_score_market_events, detect_and_score_fundamental_events, evaluate_d1_market_events, evaluate_d4_market_events
from .delivery import build_technical_daily_packet, TechnicalDailySignalPacket, TechnicalFamilyCheck, TechnicalPacketEvent

__all__ = ["EvidenceItem", "EventDirection", "EventType", "MaterialEventCandidate",
           "MaterialityCategory", "MaterialityComponents", "MaterialityResult",
           "ScoringContext", "detect_market_events", "detect_fundamental_events", "evaluate_candidate",
           "detect_and_score_market_events", "detect_and_score_fundamental_events", "evaluate_d1_market_events", "evaluate_d4_market_events",
           "build_technical_daily_packet", "TechnicalDailySignalPacket", "TechnicalFamilyCheck", "TechnicalPacketEvent"]
