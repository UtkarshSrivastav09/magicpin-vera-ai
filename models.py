from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Category Context ---

class OfferTemplate(BaseModel):
    title: str
    value: Optional[str] = None
    audience: Optional[str] = None

class VoiceProfile(BaseModel):
    tone: str
    vocab_allowed: List[str] = []
    vocab_taboo: List[str] = []

class PeerStats(BaseModel):
    avg_rating: float
    avg_reviews: int
    avg_ctr: float
    scope: Optional[str] = None

class DigestItem(BaseModel):
    id: str
    kind: str
    title: str
    source: str
    trial_n: Optional[int] = None
    patient_segment: Optional[str] = None
    summary: Optional[str] = None

class ContentItem(BaseModel):
    id: str
    title: str
    channel: str
    body: str

class SeasonalBeat(BaseModel):
    month_range: str
    note: str

class TrendSignal(BaseModel):
    query: str
    delta_yoy: float
    segment_age: Optional[str] = None

class CategoryContext(BaseModel):
    slug: str
    offer_catalog: List[OfferTemplate]
    voice: VoiceProfile
    peer_stats: PeerStats
    digest: List[DigestItem] = []
    patient_content_library: List[ContentItem] = []
    seasonal_beats: List[SeasonalBeat] = []
    trend_signals: List[TrendSignal] = []

# --- Merchant Context ---

class Identity(BaseModel):
    name: str
    city: str
    locality: str
    place_id: Optional[str] = None
    verified: bool = False
    languages: List[str] = ["en"]
    owner_first_name: Optional[str] = None

class Subscription(BaseModel):
    status: str
    plan: str
    days_remaining: int

class PerformanceSnapshot(BaseModel):
    window_days: int = 30
    views: int
    calls: int
    directions: int
    ctr: float
    delta_7d: Optional[Dict[str, float]] = None

class MerchantOffer(BaseModel):
    id: str
    title: str
    status: Literal["active", "paused", "expired"]

class ConversationTurn(BaseModel):
    ts: str
    from_role: str = Field(..., alias="from")
    body: str
    engagement: Optional[str] = None

class CustomerAggregate(BaseModel):
    total_unique_ytd: int
    lapsed_180d_plus: int
    retention_6mo_pct: float

class MerchantContext(BaseModel):
    merchant_id: str
    category_slug: str
    identity: Identity
    subscription: Subscription
    performance: PerformanceSnapshot
    offers: List[MerchantOffer]
    conversation_history: List[ConversationTurn] = []
    customer_aggregate: Optional[CustomerAggregate] = None
    signals: List[str] = []

# --- Trigger Context ---

class TriggerContext(BaseModel):
    id: str
    scope: Literal["merchant", "customer"]
    kind: str
    source: Literal["external", "internal"]
    merchant_id: str
    customer_id: Optional[str] = None
    payload: Dict[str, Any]
    urgency: int = 3
    suppression_key: str
    expires_at: str

# --- Customer Context ---

class CustomerIdentity(BaseModel):
    name: str
    phone_redacted: str
    language_pref: str = "en"

class Relationship(BaseModel):
    first_visit: str
    last_visit: str
    visits_total: int
    services_received: List[str] = []

class CustomerContext(BaseModel):
    customer_id: str
    merchant_id: str
    identity: CustomerIdentity
    relationship: Relationship
    state: Literal["new", "active", "lapsed_soft", "lapsed_hard", "churned"]
    preferences: Dict[str, Any]
    consent: Dict[str, Any]

# --- Response Models ---

class ComposedMessage(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    send_as: Literal["vera", "merchant_on_behalf"]
    trigger_id: str
    template_name: Optional[str] = None
    template_params: List[str] = []
    body: str
    cta: str
    suppression_key: str
    rationale: str

class TickResponse(BaseModel):
    actions: List[ComposedMessage]

class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str
