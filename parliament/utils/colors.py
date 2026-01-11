"""
Terminal color utilities for parliament output
"""

class Colors:
    """ANSI color codes for terminal output"""
    # Basic colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


# Faction-specific colors
FACTION_COLORS = {
    "Efficiency": Colors.CYAN,
    "Safety": Colors.RED,
    "Equity": Colors.GREEN,
    "Innovation": Colors.MAGENTA,
    "Compliance": Colors.YELLOW,
    "Speaker": Colors.BRIGHT_WHITE,
}


def colored(text: str, color: str, bold: bool = False) -> str:
    """
    Apply color to text.
    
    Args:
        text: The text to colorize
        color: ANSI color code
        bold: Whether to make text bold
        
    Returns:
        Colored text string
    """
    prefix = f"{Colors.BOLD}{color}" if bold else color
    return f"{prefix}{text}{Colors.RESET}"


def faction_colored(faction_name: str, text: str, bold: bool = False) -> str:
    """
    Color text based on faction.
    
    Args:
        faction_name: Name of the faction
        text: Text to colorize
        bold: Whether to make text bold
        
    Returns:
        Colored text string
    """
    color = FACTION_COLORS.get(faction_name, Colors.WHITE)
    return colored(text, color, bold)


def header(text: str, style: str = "main") -> str:
    """
    Create a styled header.
    
    Args:
        text: Header text
        style: "main", "section", or "subsection"
        
    Returns:
        Styled header string
    """
    if style == "main":
        return colored(f"\n{'=' * 60}\n{text}\n{'=' * 60}\n", Colors.BRIGHT_CYAN, bold=True)
    elif style == "section":
        return colored(f"\n{text}", Colors.BRIGHT_YELLOW, bold=True)
    elif style == "subsection":
        return colored(f"\n>>> {text} <<<", Colors.BRIGHT_BLUE, bold=True)
    return text


def vote_colored(choice: str) -> str:
    """
    Color vote choice appropriately.
    
    Args:
        choice: APPROVE, REJECT, or ABSTAIN
        
    Returns:
        Colored vote choice
    """
    if choice == "APPROVE":
        return colored(choice, Colors.BRIGHT_GREEN, bold=True)
    elif choice == "REJECT":
        return colored(choice, Colors.BRIGHT_RED, bold=True)
    elif choice == "ABSTAIN":
        return colored(choice, Colors.BRIGHT_YELLOW, bold=True)
    return choice


def decision_colored(passed: bool) -> str:
    """
    Color final decision.
    
    Args:
        passed: Whether the bill passed
        
    Returns:
        Colored decision text
    """
    if passed:
        return colored("✓ PASSED", Colors.BRIGHT_GREEN, bold=True)
    else:
        return colored("✗ REJECTED", Colors.BRIGHT_RED, bold=True)
