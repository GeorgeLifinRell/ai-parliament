"""
Test debate functionality
"""
from uuid import uuid4
from parliament.core.bill import Bill, BillStatus
from parliament.core.debate import DebateArgument
from parliament.procedure.speaker import Speaker, Phase


def test_debate_argument_creation():
    """Test creating a valid debate argument"""
    bill_id = uuid4()
    arg = DebateArgument(
        id=uuid4(),
        bill_id=bill_id,
        bill_version=1,
        speaker_faction="Safety",
        round_number=1,
        argument="We must ensure robust safety measures.",
        targeted_factions=["Innovation", "Efficiency"]
    )
    
    assert arg.speaker_faction == "Safety"
    assert arg.round_number == 1
    assert len(arg.targeted_factions) == 2


def test_speaker_debate_phase():
    """Test that Speaker properly manages debate phase"""
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
    
    speaker = Speaker(bill, max_debate_rounds=2)
    
    # Initially should be in INTRODUCTION
    assert speaker.phase == Phase.INTRODUCTION
    
    # Move to FACTION_STATEMENTS
    speaker.advance_phase()
    assert speaker.phase == Phase.FACTION_STATEMENTS
    
    # Move to DEBATE
    speaker.advance_phase()
    assert speaker.phase == Phase.DEBATE
    
    # Speaker can only set debate order during DEBATE phase
    speaker.set_debate_order(["Efficiency", "Safety", "Equity"])
    assert speaker.debate_order == ["Efficiency", "Safety", "Equity"]
    
    # Test debate round tracking
    assert speaker.debate_round == 0
    assert speaker.next_debate_round() == True
    assert speaker.debate_round == 1
    
    # Should continue for max_debate_rounds
    assert speaker.next_debate_round() == False
    assert speaker.debate_round == 2


def test_debate_allows_empty_targets():
    """Test that debate arguments can address all factions"""
    bill_id = uuid4()
    arg = DebateArgument(
        id=uuid4(),
        bill_id=bill_id,
        bill_version=1,
        speaker_faction="Innovation",
        round_number=1,
        argument="This benefits everyone.",
        targeted_factions=[]  # Empty means all factions
    )
    
    assert arg.targeted_factions == []
