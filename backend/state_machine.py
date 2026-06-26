"""
智能体状态机 — 18 个状态
"""

from __future__ import annotations

from enum import Enum


class AgentState(str, Enum):
    AGENT_RECEIVED = "agent_received"
    AGENT_CLASSIFYING_FILE = "agent_classifying_file"
    AGENT_RENDERING_PDF_IF_NEEDED = "agent_rendering_pdf_if_needed"
    AGENT_PREPROCESSING_VISIBLE_IMAGE = "agent_preprocessing_visible_image"
    AGENT_EXTRACTING_VISIBLE_FIELDS = "agent_extracting_visible_fields"
    AGENT_EXTRACTING_PDF_TEXT_LAYER_OPTIONAL = "agent_extracting_pdf_text_layer_optional"
    AGENT_CHECKING_PDF_SIGNATURE_REFERENCE_OPTIONAL = "agent_checking_pdf_signature_reference_optional"
    AGENT_NORMALIZING_FIELDS = "agent_normalizing_fields"
    AGENT_QUERYING_OFFICIAL_RECORD = "agent_querying_official_record"
    AGENT_CROSS_CHECKING_SOURCES = "agent_cross_checking_sources"
    AGENT_COMPARING_WITH_OFFICIAL_RECORD = "agent_comparing_with_official_record"
    AGENT_DECISION_MAKING = "agent_decision_making"

    APPROVED = "approved"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    MANUAL_APPROVED = "manual_approved"
    MANUAL_REJECTED = "manual_rejected"
    RESUBMIT_REQUIRED = "resubmit_required"
    FAILED = "failed"


TERMINAL_STATES = {
    AgentState.APPROVED,
    AgentState.MANUAL_REVIEW_REQUIRED,
    AgentState.MANUAL_APPROVED,
    AgentState.MANUAL_REJECTED,
    AgentState.RESUBMIT_REQUIRED,
    AgentState.FAILED,
}

STATE_TRANSITIONS: dict[AgentState, list[AgentState]] = {
    AgentState.AGENT_RECEIVED: [
        AgentState.AGENT_CLASSIFYING_FILE,
        AgentState.FAILED,
    ],
    AgentState.AGENT_CLASSIFYING_FILE: [
        AgentState.AGENT_RENDERING_PDF_IF_NEEDED,
        AgentState.AGENT_PREPROCESSING_VISIBLE_IMAGE,
        AgentState.RESUBMIT_REQUIRED,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_RENDERING_PDF_IF_NEEDED: [
        AgentState.AGENT_PREPROCESSING_VISIBLE_IMAGE,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_PREPROCESSING_VISIBLE_IMAGE: [
        AgentState.AGENT_EXTRACTING_VISIBLE_FIELDS,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_EXTRACTING_VISIBLE_FIELDS: [
        AgentState.AGENT_EXTRACTING_PDF_TEXT_LAYER_OPTIONAL,
        AgentState.AGENT_NORMALIZING_FIELDS,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_EXTRACTING_PDF_TEXT_LAYER_OPTIONAL: [
        AgentState.AGENT_CHECKING_PDF_SIGNATURE_REFERENCE_OPTIONAL,
        AgentState.AGENT_NORMALIZING_FIELDS,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_CHECKING_PDF_SIGNATURE_REFERENCE_OPTIONAL: [
        AgentState.AGENT_NORMALIZING_FIELDS,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_NORMALIZING_FIELDS: [
        AgentState.AGENT_QUERYING_OFFICIAL_RECORD,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_QUERYING_OFFICIAL_RECORD: [
        AgentState.AGENT_CROSS_CHECKING_SOURCES,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_CROSS_CHECKING_SOURCES: [
        AgentState.AGENT_COMPARING_WITH_OFFICIAL_RECORD,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_COMPARING_WITH_OFFICIAL_RECORD: [
        AgentState.AGENT_DECISION_MAKING,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.AGENT_DECISION_MAKING: [
        AgentState.APPROVED,
        AgentState.MANUAL_REVIEW_REQUIRED,
        AgentState.FAILED,
    ],
    AgentState.APPROVED: [],
    AgentState.MANUAL_REVIEW_REQUIRED: [
        AgentState.MANUAL_APPROVED,
        AgentState.MANUAL_REJECTED,
        AgentState.RESUBMIT_REQUIRED,
    ],
    AgentState.MANUAL_APPROVED: [],
    AgentState.MANUAL_REJECTED: [],
    AgentState.RESUBMIT_REQUIRED: [AgentState.AGENT_RECEIVED],
    AgentState.FAILED: [],
}


def can_transition(from_state: AgentState, to_state: AgentState) -> bool:
    return to_state in STATE_TRANSITIONS.get(from_state, [])


class InvalidStateTransition(Exception):
    def __init__(self, from_state: AgentState, to_state: AgentState):
        super().__init__(f"非法状态转换: {from_state.value} -> {to_state.value}")
        self.from_state = from_state
        self.to_state = to_state
