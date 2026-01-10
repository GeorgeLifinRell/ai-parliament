"""
Test Speaker's veto power assignment functionality
"""
from uuid import uuid4
from parliament.core.bill import Bill, BillStatus
from parliament.procedure.speaker import Speaker


def test_speaker_veto_power_assignment():
    """Test that Speaker can assign and revoke veto power"""
    bill = Bill(
        id=uuid4(),
        title="Test Bill",
        proposal="Test proposal",
        assumptions=["test"],
        intended_outcomes=["test"],
        known_risks=["test"],
        unknowns=["test"],
        status=BillStatus.DRAFT
    )
    
    speaker = Speaker(bill)
    
    # Initially no veto factions
    assert len(speaker.get_veto_factions()) == 0
    
    # Assign veto power to Safety
    speaker.assign_veto_power("Safety")
    assert "Safety" in speaker.get_veto_factions()
    assert len(speaker.get_veto_factions()) == 1
    
    # Assign veto power to Compliance
    speaker.assign_veto_power("Compliance")
    assert "Safety" in speaker.get_veto_factions()
    assert "Compliance" in speaker.get_veto_factions()
    assert len(speaker.get_veto_factions()) == 2
    
    # Revoke veto power from Safety
    speaker.revoke_veto_power("Safety")
    assert "Safety" not in speaker.get_veto_factions()
    assert "Compliance" in speaker.get_veto_factions()
    assert len(speaker.get_veto_factions()) == 1


def test_veto_power_returns_copy():
    """Test that get_veto_factions returns a copy, not the original set"""
    bill = Bill(
        id=uuid4(),
        title="Test Bill",
        proposal="Test proposal",
        assumptions=["test"],
        intended_outcomes=["test"],
        known_risks=["test"],
        unknowns=["test"],
        status=BillStatus.DRAFT
    )
    
    speaker = Speaker(bill)
    speaker.assign_veto_power("Safety")
    
    # Get veto factions and try to modify it
    veto_set = speaker.get_veto_factions()
    veto_set.add("Hacker")
    
    # Original should be unchanged
    assert "Hacker" not in speaker.get_veto_factions()
    assert len(speaker.get_veto_factions()) == 1


def test_duplicate_veto_assignment():
    """Test that assigning veto power multiple times to same faction is idempotent"""
    bill = Bill(
        id=uuid4(),
        title="Test Bill",
        proposal="Test proposal",
        assumptions=["test"],
        intended_outcomes=["test"],
        known_risks=["test"],
        unknowns=["test"],
        status=BillStatus.DRAFT
    )
    
    speaker = Speaker(bill)
    
    # Assign same faction multiple times
    speaker.assign_veto_power("Safety")
    speaker.assign_veto_power("Safety")
    speaker.assign_veto_power("Safety")
    
    # Should still only have one
    assert len(speaker.get_veto_factions()) == 1
    assert "Safety" in speaker.get_veto_factions()
