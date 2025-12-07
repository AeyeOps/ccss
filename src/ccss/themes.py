"""Custom theme definitions for CCSS.

CC Tribute Theme
================
A dark theme inspired by Claude Code's aesthetic.

Color Philosophy:
- Deep blacks and grays for backgrounds (minimal eye strain)
- Warm orange accents (tribute to Claude's signature color)
- High contrast text for readability
- Semantic colors shifted warm to maintain cohesion

Contrast Ratios (WCAG AA requires 4.5:1 for normal text):
- foreground on background: ~18:1 (excellent)
- foreground on surface: ~15:1 (excellent)
- primary on background: ~7:1 (good for interactive elements)
- primary on surface: ~6:1 (acceptable for buttons/links)

Layer Hierarchy (darkest to lightest):
1. background (#0d0d0d) - Base layer, app background
2. surface (#1a1a1a) - Cards, containers, input fields
3. panel (#262626) - Nested panels, modals, elevated surfaces
"""

from textual.theme import Theme

# Claude Code Tribute Theme
# -------------------------
# A meticulous dark theme with orange accents

CC_TRIBUTE_THEME = Theme(
    name="cc-tribute",
    # Base layer - the darkest, used for app background
    background="#0d0d0d",
    # Surface layer - slightly lifted, for containers and cards
    surface="#1a1a1a",
    # Panel layer - for nested elements, modals, elevated surfaces
    panel="#262626",
    # Text color - light gray, high contrast on dark backgrounds
    foreground="#e6e6e6",
    # Primary - warm orange, Claude's signature color
    # Used for primary buttons, links, focus indicators
    primary="#e07a3c",
    # Secondary - neutral gray for de-emphasized elements
    # Used for borders, disabled states, secondary text
    secondary="#8c8c8c",
    # Accent - lighter orange for highlights
    # Used for hover states, selection backgrounds, badges
    accent="#f5a060",
    # Semantic: Success - muted forest green
    # Warm-shifted to stay harmonious with orange palette
    success="#5eb85e",
    # Semantic: Warning - amber/gold
    # Orange-adjacent, natural pairing with primary
    warning="#e6a832",
    # Semantic: Error - red-orange
    # Stays in warm family, distinct but cohesive
    error="#d94a3d",
    # Dark theme flag
    dark=True,
    # Custom variables for fine-tuning
    variables={
        # Cursor styling
        "block-cursor-foreground": "#0d0d0d",
        "block-cursor-background": "#e07a3c",
        "block-cursor-text-style": "bold",
        # Input selection - orange tint
        "input-selection-background": "#e07a3c 30%",
        # Note: Scrollbar styling done via CSS properties in app.py
        # Footer styling
        "footer-background": "#1a1a1a",
        "footer-key-foreground": "#e07a3c",
        "footer-key-background": "#262626",
        "footer-description-foreground": "#8c8c8c",
        # Border colors
        "border": "#404040",
        "border-blurred": "#333333",
        # Button styling
        "button-color-foreground": "#0d0d0d",
        "button-focus-text-style": "bold",
    },
)

# All custom themes to register
CUSTOM_THEMES = [CC_TRIBUTE_THEME]
