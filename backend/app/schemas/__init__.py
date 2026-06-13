# Appointment schemas
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse

# Lead schemas
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse

# Property schemas
from app.schemas.property import PropertyCreate, PropertyResponse

# Agent schemas
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

# Message schemas
from app.schemas.message import MessageCreate, MessageResponse

# PropertyMedia schemas
from app.schemas.property_media import PropertyMediaCreate, PropertyMediaResponse

# AIInteraction schemas
from app.schemas.ai_interaction import AIInteractionCreate, AIInteractionResponse

# FollowUpLog schemas
from app.schemas.follow_up_log import FollowUpLogCreate, FollowUpLogResponse

# LeadActivity schemas
from app.schemas.lead_activity import LeadActivityResponse

# Auth schemas
from app.schemas.auth import UserLogin, Token, TokenData

# Search & Pagination schemas
from app.schemas.search import PropertySearchParams, Pagination, PaginatedResponse

__all__ = [
    # Appointment
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    # Lead
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    # Property
    "PropertyCreate",
    "PropertyResponse",
    # Agent
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    # Message
    "MessageCreate",
    "MessageResponse",
    # PropertyMedia
    "PropertyMediaCreate",
    "PropertyMediaResponse",
    # AIInteraction
    "AIInteractionCreate",
    "AIInteractionResponse",
    # FollowUpLog
    "FollowUpLogCreate",
    "FollowUpLogResponse",
    # LeadActivity
    "LeadActivityResponse",
    # Auth
    "UserLogin",
    "Token",
    "TokenData",
    # Search & Pagination
    "PropertySearchParams",
    "Pagination",
    "PaginatedResponse",
]
