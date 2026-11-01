"""Original save-state console tokens. Independent of project data and CLI colors."""

from rich.style import Style
from rich.syntax import SyntaxTheme, TokenType
from textual.theme import Theme

DARK = {
    "background": "#0B1020",
    "surface": "#131B2E",
    "slot": "#1C2940",
    "frame": "#34465E",
    "text": "#E8F0FF",
    "muted": "#9AAFC8",
    "primary": "#73E0C4",
    "protected": "#A99CFF",
    "warning": "#F3C969",
    "success": "#83E6A0",
    "error": "#F37D92",
    "added": "#83E6A0",
    "modified": "#F3C969",
    "deleted": "#F37D92",
    "type": "#A99CFF",
    "metadata": "#A99CFF",
    "saved": "#9AAFC8",
    "conflict": "#F37D92",
}
LIGHT = {
    "background": "#E9E5D5",
    "surface": "#FAF7EE",
    "slot": "#E0DECF",
    "frame": "#88928B",
    "text": "#182C35",
    "muted": "#4D6269",
    "primary": "#116D5A",
    "protected": "#5E4E98",
    "warning": "#805100",
    "success": "#22613A",
    "error": "#A52B4A",
    "added": "#22613A",
    "modified": "#805100",
    "deleted": "#A52B4A",
    "type": "#5E4E98",
    "metadata": "#5E4E98",
    "saved": "#4D6269",
    "conflict": "#A52B4A",
}


def console_theme(*, light: bool = False) -> Theme:
    colors = LIGHT if light else DARK
    return Theme(
        name="timemachine-light" if light else "timemachine",
        primary=colors["primary"],
        secondary=colors["protected"],
        background=colors["background"],
        surface=colors["surface"],
        panel=colors["slot"],
        foreground=colors["text"],
        success=colors["success"],
        warning=colors["warning"],
        error=colors["error"],
        accent=colors["protected"],
        dark=not light,
        variables={"frame": colors["frame"], "ink-muted": colors["muted"]},
    )


class SaveStateSyntax(SyntaxTheme):
    """Semantic diff/source colors share the UI palette in both themes."""

    def __init__(self, colors: dict[str, str]):
        self.colors = colors

    def get_style_for_token(self, token_type: TokenType) -> Style:
        token = ".".join(token_type)
        color = (
            "added"
            if "Inserted" in token
            else "deleted"
            if "Deleted" in token
            else "protected"
            if any(t in token for t in ("Heading", "Subheading", "Keyword"))
            else "primary"
            if "String" in token
            else "warning"
            if "Number" in token
            else "muted"
            if "Comment" in token
            else "text"
        )
        return Style(color=self.colors[color], bold="Heading" in token or "Keyword" in token)

    def get_background_style(self) -> Style:
        return Style(bgcolor=self.colors["surface"])
