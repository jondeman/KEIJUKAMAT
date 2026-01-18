"""
State machine for KonseptiKeiju pipeline.

Defines valid phase transitions and enforces pipeline flow.
"""

from src.core.models import Phase


# Valid phase transitions
TRANSITIONS: dict[Phase, list[Phase]] = {
    Phase.INPUT: [Phase.VALIDATE],
    Phase.VALIDATE: [Phase.CHECK_ARCHIVE, Phase.ERROR],
    Phase.CHECK_ARCHIVE: [Phase.RESEARCH, Phase.STRATEGIZE],  # Skip research if cached
    Phase.RESEARCH: [Phase.STRATEGIZE, Phase.ERROR],
    Phase.STRATEGIZE: [Phase.CREATE, Phase.ERROR],
    Phase.CREATE: [Phase.VISUALIZE, Phase.ERROR],
    Phase.VISUALIZE: [Phase.COMPOSE_PITCH, Phase.ERROR],
    Phase.COMPOSE_PITCH: [Phase.PACKAGE, Phase.ERROR],
    Phase.PACKAGE: [Phase.DELIVER, Phase.ERROR],
    Phase.DELIVER: [Phase.DONE, Phase.ERROR],
    Phase.DONE: [],  # Terminal state
    Phase.ERROR: [],  # Terminal state (can be reset for retry)
}


class StateMachine:
    """
    State machine for managing pipeline phase transitions.
    
    Ensures valid transitions and provides phase metadata.
    """

    @staticmethod
    def can_transition(from_phase: Phase, to_phase: Phase) -> bool:
        """
        Check if a transition is valid.
        
        Args:
            from_phase: Current phase
            to_phase: Target phase
            
        Returns:
            True if transition is valid
        """
        valid_targets = TRANSITIONS.get(from_phase, [])
        return to_phase in valid_targets

    @staticmethod
    def get_valid_transitions(phase: Phase) -> list[Phase]:
        """
        Get valid transition targets for a phase.
        
        Args:
            phase: Current phase
            
        Returns:
            List of valid target phases
        """
        return TRANSITIONS.get(phase, [])

    @staticmethod
    def is_terminal(phase: Phase) -> bool:
        """Check if phase is terminal (no valid transitions)."""
        return phase in (Phase.DONE, Phase.ERROR)

    @staticmethod
    def get_next_phase(current: Phase, skip_research: bool = False) -> Phase:
        """
        Get the default next phase.
        
        Args:
            current: Current phase
            skip_research: If True, skip research phase (use cached)
            
        Returns:
            Next phase in normal flow
        """
        normal_flow = {
            Phase.INPUT: Phase.VALIDATE,
            Phase.VALIDATE: Phase.CHECK_ARCHIVE,
            Phase.CHECK_ARCHIVE: Phase.STRATEGIZE if skip_research else Phase.RESEARCH,
            Phase.RESEARCH: Phase.STRATEGIZE,
            Phase.STRATEGIZE: Phase.CREATE,
            Phase.CREATE: Phase.VISUALIZE,
            Phase.VISUALIZE: Phase.COMPOSE_PITCH,
            Phase.COMPOSE_PITCH: Phase.PACKAGE,
            Phase.PACKAGE: Phase.DELIVER,
            Phase.DELIVER: Phase.DONE,
        }
        return normal_flow.get(current, Phase.ERROR)

    @staticmethod
    def get_phase_description(phase: Phase) -> str:
        """Get human-readable description of a phase."""
        descriptions = {
            Phase.INPUT: "Receiving user input",
            Phase.VALIDATE: "Validating input and access",
            Phase.CHECK_ARCHIVE: "Checking for cached research",
            Phase.RESEARCH: "Conducting deep research on company",
            Phase.STRATEGIZE: "Assigning strategic tensions to concept slots",
            Phase.CREATE: "Generating video concepts",
            Phase.VISUALIZE: "Creating visual one-pagers",
            Phase.COMPOSE_PITCH: "Composing pitch email",
            Phase.PACKAGE: "Packaging deliverables",
            Phase.DELIVER: "Sending to user",
            Phase.DONE: "Complete",
            Phase.ERROR: "Error encountered",
        }
        return descriptions.get(phase, "Unknown phase")

    @staticmethod
    def get_phase_emoji(phase: Phase) -> str:
        """Get emoji for phase visualization."""
        emojis = {
            Phase.INPUT: "📥",
            Phase.VALIDATE: "✅",
            Phase.CHECK_ARCHIVE: "📚",
            Phase.RESEARCH: "🔍",
            Phase.STRATEGIZE: "🎯",
            Phase.CREATE: "💡",
            Phase.VISUALIZE: "🎨",
            Phase.COMPOSE_PITCH: "✉️",
            Phase.PACKAGE: "📦",
            Phase.DELIVER: "🚀",
            Phase.DONE: "🎉",
            Phase.ERROR: "❌",
        }
        return emojis.get(phase, "❓")

    @staticmethod
    def get_progress_percentage(phase: Phase) -> int:
        """Get completion percentage for a phase."""
        percentages = {
            Phase.INPUT: 0,
            Phase.VALIDATE: 5,
            Phase.CHECK_ARCHIVE: 10,
            Phase.RESEARCH: 30,
            Phase.STRATEGIZE: 40,
            Phase.CREATE: 60,
            Phase.VISUALIZE: 80,
            Phase.COMPOSE_PITCH: 90,
            Phase.PACKAGE: 95,
            Phase.DELIVER: 98,
            Phase.DONE: 100,
            Phase.ERROR: -1,
        }
        return percentages.get(phase, 0)
