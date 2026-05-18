from enum import Enum


class LeadStatus(str, Enum):
    PENDING = "pending"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    CALLBACK_REQUESTED = "callback_requested"
    UNREACHABLE = "unreachable"


class FundCategory(str, Enum):
    EQUITY = "equity"
    DEBT = "debt"
    HYBRID = "hybrid"
    INDEX = "index"
    ELSS = "elss"
    UNKNOWN = "unknown"


class CallDirection(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
