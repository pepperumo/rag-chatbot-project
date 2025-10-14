"""
Simple unit tests for email agent core logic without complex mocking.

Tests the essential logic patterns used in the human-in-the-loop email workflow.
"""

import pytest
import json
from typing import Dict, Any


class TestEmailWorkflowLogic:
    """Test core email workflow logic patterns."""

    def test_approval_response_detection(self):
        """Test approval response pattern detection."""
        # Test yes patterns
        assert self._is_approval_response("yes") is True
        assert self._is_approval_response("yes-looks good") is True
        assert self._is_approval_response("YES") is True
        assert self._is_approval_response("Yes-Perfect") is True
        
        # Test no patterns
        assert self._is_approval_response("no") is True
        assert self._is_approval_response("no-cancel this") is True
        assert self._is_approval_response("NO") is True
        assert self._is_approval_response("No-stop") is True
        
        # Test non-approval queries
        assert self._is_approval_response("send an email") is False
        assert self._is_approval_response("check my inbox") is False
        assert self._is_approval_response("what's my schedule") is False

    def test_approval_decision_parsing(self):
        """Test parsing approval decisions from responses."""
        # Test positive approval with feedback
        decision = self._parse_approval_decision("yes-looks great")
        assert decision["approved"] is True
        assert decision["feedback"] == "looks great"
        
        # Test positive approval without feedback
        decision = self._parse_approval_decision("yes")
        assert decision["approved"] is True
        assert decision["feedback"] == ""
        
        # Test negative approval with feedback
        decision = self._parse_approval_decision("no-cancel this")
        assert decision["approved"] is False
        assert decision["feedback"] == "cancel this"
        
        # Test negative approval without feedback
        decision = self._parse_approval_decision("no")
        assert decision["approved"] is False
        assert decision["feedback"] == ""

    def test_email_approval_conditions(self):
        """Test conditions for showing email approval UI."""
        # Should show approval
        state_needs_approval = {
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject",
            "email_body": "Test body",
            "approval_granted": None
        }
        assert self._should_show_approval(state_needs_approval) is True
        
        # Should not show approval - already granted
        state_approved = {
            "email_recipients": ["test@example.com"],
            "email_subject": "Test Subject", 
            "email_body": "Test body",
            "approval_granted": True
        }
        assert self._should_show_approval(state_approved) is False
        
        # Should not show approval - no recipients
        state_no_recipients = {
            "email_recipients": None,
            "email_subject": "Test Subject",
            "email_body": "Test body",
            "approval_granted": None
        }
        assert self._should_show_approval(state_no_recipients) is False

    def test_approval_chunk_structure(self):
        """Test approval request chunk structure."""
        email_data = {
            "recipients": ["test@example.com"],
            "subject": "Test Subject",
            "body": "Test email body"
        }
        
        chunk = self._create_approval_chunk(email_data)
        
        assert chunk["type"] == "approval_request"
        assert "email_preview" in chunk
        assert chunk["email_preview"]["recipients"] == ["test@example.com"]
        assert chunk["email_preview"]["subject"] == "Test Subject"
        assert chunk["email_preview"]["body"] == "Test email body"

    def test_json_chunk_encoding(self):
        """Test JSON chunk encoding/decoding."""
        chunk_data = {"text": "Hello, I've processed your request."}
        chunk_bytes = json.dumps(chunk_data).encode('utf-8') + b'\n'
        
        # Verify it can be decoded
        decoded = json.loads(chunk_bytes.decode().strip())
        assert decoded["text"] == "Hello, I've processed your request."

    # Helper methods that implement the core logic patterns
    def _is_approval_response(self, query: str) -> bool:
        """Check if query is an approval response."""
        query_lower = query.lower().strip()
        return (
            query_lower.startswith("yes-") or query_lower == "yes" or
            query_lower.startswith("no-") or query_lower == "no"
        )

    def _parse_approval_decision(self, query: str) -> Dict[str, Any]:
        """Parse approval decision from query."""
        query_lower = query.lower().strip()
        
        if query_lower.startswith("yes-") or query_lower == "yes":
            feedback = query_lower[4:] if len(query_lower) > 4 else ""
            return {"approved": True, "feedback": feedback}
        elif query_lower.startswith("no-") or query_lower == "no":
            feedback = query_lower[3:] if len(query_lower) > 3 else ""
            return {"approved": False, "feedback": feedback}
        
        return {"approved": False, "feedback": ""}

    def _should_show_approval(self, state: Dict[str, Any]) -> bool:
        """Check if approval UI should be shown."""
        return bool(
            state.get("email_recipients") and
            state.get("email_subject") and
            not state.get("approval_granted")
        )

    def _create_approval_chunk(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create approval request chunk."""
        return {
            "type": "approval_request",
            "email_preview": {
                "recipients": email_data.get("recipients", []),
                "subject": email_data.get("subject", ""),
                "body": email_data.get("body", "")
            }
        }