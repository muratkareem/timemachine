from timemachine.tui.design import DARK, LIGHT, SaveStateSyntax, console_theme


def luminance(hex_color):
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def test_semantic_text_tokens_have_readable_surface_contrast():
    for colors in (DARK, LIGHT):
        for key in ("text", "muted", "primary", "protected", "warning", "error", "added"):
            a, b = sorted([luminance(colors[key]), luminance(colors["surface"])])
            assert (b + 0.05) / (a + 0.05) >= 4.5, (key, colors[key])


def test_syntax_and_terminal_theme_share_semantics():
    for colors, light in ((DARK, False), (LIGHT, True)):
        syntax = SaveStateSyntax(colors)
        assert (
            syntax.get_style_for_token(("Generic", "Deleted")).color.triplet.hex
            == colors["deleted"].lower()
        )
        assert console_theme(light=light).primary == colors["primary"]
