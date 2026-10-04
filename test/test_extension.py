from pathlib import Path

import pytest
from bs4 import BeautifulSoup, Tag
from sphinx.errors import ConfigError
from sphinx.testing.util import SphinxTestApp

import sphinx_eu_ai_label


def soup(app: SphinxTestApp, page: str = "index") -> BeautifulSoup:
    return BeautifulSoup((Path(app.outdir) / f"{page}.html").read_text(), "html.parser")


def labels(app: SphinxTestApp, page: str = "index") -> list[Tag]:
    return soup(app, page).select(".eu-ai-label")


def one(tag: Tag, selector: str) -> Tag:
    found = tag.select_one(selector)
    assert found is not None
    return found


def icon_srcs(label: Tag) -> list[str]:
    return [str(img["src"]) for img in label.select("img")]


@pytest.mark.sphinx("html", testroot="basic")
def test_default_directive(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[0]
    assert label.name == "div"
    assert label["class"] == [
        "eu-ai-label",
        "eu-ai-label-generated",
        "eu-ai-label-block",
        "eu-ai-label-align-left",
    ]
    # The icon has its own wording, so there's no text label by default
    assert label.select_one(".eu-ai-label-text") is None
    # Auto variant: black for light mode, white for dark mode
    assert icon_srcs(label) == [
        "_static/eu_ai_label/icons/generated-black.svg",
        "_static/eu_ai_label/icons/generated-white.svg",
    ]
    for img in label.select("img"):
        assert img["alt"] == "AI-generated"
        assert img["style"] == "height: 2.5em"


@pytest.mark.sphinx("html", testroot="basic")
def test_directive_without_argument_is_basic(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[1]
    assert "eu-ai-label-basic" in label["class"]
    assert label.select_one(".eu-ai-label-text") is None
    assert {img["alt"] for img in label.select("img")} == {"AI"}


@pytest.mark.sphinx("html", testroot="basic")
def test_directive_options(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[2]
    assert label["class"][-3:] == ["eu-ai-label-align-right", "extra", "another"]
    assert icon_srcs(label) == ["_static/eu_ai_label/icons/basic-white.svg"]
    # Basic icon comes after the text, so it reads "Summary generated with AI"
    assert one(label, ".eu-ai-label-text").get_text() == "Summary generated with"
    assert one(label, "img")["alt"] == "AI"
    children = [child for child in label.children if isinstance(child, Tag)]
    assert [child.name for child in children] == ["span", "img"]


@pytest.mark.sphinx("html", testroot="basic")
def test_empty_text_shows_icon_only(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[3]
    assert label.select_one(".eu-ai-label-text") is None
    assert {img["alt"] for img in label.select("img")} == {"AI-modified"}


@pytest.mark.sphinx("html", testroot="basic")
def test_role(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[4]
    assert label.name == "span"
    assert label.parent is not None
    assert label.parent.name == "p"
    assert "eu-ai-label-inline" in label["class"]
    assert label.select_one(".eu-ai-label-text") is None
    assert {img["alt"] for img in label.select("img")} == {"AI-generated"}
    # Smaller than block labels, so it doesn't stretch the line as much
    assert {img["style"] for img in label.select("img")} == {"height: 1.75em"}


@pytest.mark.sphinx("html", testroot="basic")
def test_icon_paths_relative_to_page(app: SphinxTestApp) -> None:
    app.build()
    assert icon_srcs(labels(app, "sub/page")[0])[0] == "../_static/eu_ai_label/icons/modified-black.svg"


@pytest.mark.sphinx("html", testroot="basic")
def test_static_files(app: SphinxTestApp) -> None:
    app.build()
    assert (Path(app.outdir) / "_static" / "eu_ai_label" / "eu_ai_label.css").is_file()
    stylesheets = [link["href"] for link in soup(app).select("link[rel=stylesheet]")]
    assert any(str(href).startswith("_static/eu_ai_label/eu_ai_label.css") for href in stylesheets)


@pytest.mark.sphinx(
    "html",
    testroot="basic",
    confoverrides={
        "eu_ai_label_variant": "black-50",
        "eu_ai_label_size": "2rem",
        "eu_ai_label_inline_size": "1.2rem",
        "eu_ai_label_texts": {"generated": "Généré par IA"},
    },
)
def test_config(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[0]
    assert one(label, ".eu-ai-label-text").get_text() == "Généré par IA"
    assert icon_srcs(label) == ["_static/eu_ai_label/icons/generated-black-50.svg"]
    img = one(label, "img")
    # Alt text describes the icon, whatever the label says
    assert img["alt"] == "AI-generated"
    assert img["style"] == "height: 2rem"
    assert {img["style"] for img in labels(app)[4].select("img")} == {"height: 1.2rem"}
    # Explicit options still win over config
    assert icon_srcs(labels(app)[2]) == ["_static/eu_ai_label/icons/basic-white.svg"]


@pytest.mark.sphinx("html", testroot="myst")
def test_myst(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[0]
    assert "eu-ai-label-modified" in label["class"]
    assert one(label, ".eu-ai-label-text").get_text() == "Illustrations modified with AI"


@pytest.mark.sphinx("text", testroot="basic")
def test_text_builder_fallback(app: SphinxTestApp) -> None:
    app.build()
    output = (Path(app.outdir) / "index.txt").read_text()
    assert "AI-generated\n\nAI\n\nSummary generated with AI\n\nAI-modified\n" in output
    assert "This paragraph was AI-generated." in output
    assert "Paragraph written with AI" in output
    assert "Illustrations modified with AI" in output


@pytest.mark.sphinx("html", testroot="errors")
def test_unknown_kind(app: SphinxTestApp) -> None:
    app.build()
    warnings = app.warning.getvalue()
    assert "Unknown AI label kind 'nonsense'" in warnings
    assert "Unknown AI label kind 'rubbish'" in warnings
    assert "Unknown AI label variant 'purple'" in warnings
    assert "Expected an AI label kind and optional variant, not 'generated white extra'" in warnings
    assert "Unknown AI label kind ''" in warnings
    assert labels(app) == []


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"eu_ai_label_variant": "purple"}, "eu_ai_label_variant must be one of"),
        ({"eu_ai_label_texts": {"invented": "x"}}, "eu_ai_label_texts has unknown kinds: invented"),
    ],
)
def test_invalid_config(make_app, rootdir: Path, overrides: dict, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        make_app("html", srcdir=rootdir / "test-basic", confoverrides=overrides)


def test_setup_metadata(make_app, rootdir: Path) -> None:
    app = make_app("html", srcdir=rootdir / "test-basic")
    metadata = app.extensions["sphinx_eu_ai_label"]
    assert metadata.version == sphinx_eu_ai_label.__version__
    assert metadata.parallel_read_safe
    assert metadata.parallel_write_safe


@pytest.mark.sphinx("html", testroot="basic")
def test_icons_bundled_and_copied(app: SphinxTestApp) -> None:
    app.build()
    for kind in sphinx_eu_ai_label.KINDS:
        for variant in sphinx_eu_ai_label.VARIANTS[1:]:  # Everything except "auto"
            path = sphinx_eu_ai_label.icon_path(kind, variant)
            assert (sphinx_eu_ai_label.STATIC_DIR / path).is_file()
            assert (Path(app.outdir) / "_static" / path).is_file()


@pytest.mark.sphinx("text", testroot="myst")
def test_text_builder_fallback_uses_custom_text(app: SphinxTestApp) -> None:
    app.build()
    assert "Illustrations modified with AI" in (Path(app.outdir) / "index.txt").read_text()


@pytest.mark.sphinx("html", testroot="basic")
def test_role_variant(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[5]
    assert "eu-ai-label-inline" in label["class"]
    assert icon_srcs(label) == ["_static/eu_ai_label/icons/generated-white.svg"]
    assert label.select_one(".eu-ai-label-text") is None


@pytest.mark.sphinx("html", testroot="basic")
def test_role_text(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[6]
    assert "eu-ai-label-basic" in label["class"]
    # Basic icon still comes after the text
    children = [child for child in label.children if isinstance(child, Tag)]
    assert [child.name for child in children] == ["span", "img", "img"]
    assert one(label, ".eu-ai-label-text").get_text() == "Paragraph written with"


@pytest.mark.sphinx("html", testroot="basic")
def test_role_text_and_variant(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[7]
    assert one(label, ".eu-ai-label-text").get_text() == "Illustrations modified with AI"
    assert icon_srcs(label) == ["_static/eu_ai_label/icons/modified-black-50.svg"]


@pytest.mark.sphinx("html", testroot="myst")
def test_myst_role(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[1]
    assert "eu-ai-label-inline" in label["class"]
    assert one(label, ".eu-ai-label-text").get_text() == "Caption written with"
    assert icon_srcs(label) == ["_static/eu_ai_label/icons/basic-white.svg"]


@pytest.mark.sphinx("html", testroot="basic")
def test_auto_variant_shows_one_icon_without_css(app: SphinxTestApp) -> None:
    app.build()
    light, dark = labels(app)[0].select("img")
    # Browsers hide [hidden] natively, so without the stylesheet only the black icon shows
    assert not light.has_attr("hidden")
    assert dark.has_attr("hidden")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_stylesheet_follows_theme_switches(theme: str) -> None:
    # Furo sets data-theme on <body>, PyData and Book on <html>; an attribute selector matches either
    css = (sphinx_eu_ai_label.STATIC_DIR / sphinx_eu_ai_label.CSS_FILE).read_text()
    assert f'[data-theme="{theme}"] .eu-ai-label img.eu-ai-label-icon-{theme}' in css


# gettext needs its own srcdir, as its environment is incompatible with the HTML builds' doctrees
@pytest.mark.sphinx("gettext", testroot="basic", srcdir="basic-gettext")
def test_text_extracted_for_translation(app: SphinxTestApp) -> None:
    app.build()
    assert 'msgid "Summary generated with"' in (Path(app.outdir) / "index.pot").read_text()


@pytest.mark.sphinx("html", testroot="i18n")
def test_text_translated(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app)[0]
    assert one(label, ".eu-ai-label-text").get_text() == "Résumé généré avec"
    # Alt text describes the icon, so isn't translated
    assert one(label, "img")["alt"] == "AI"


@pytest.mark.sphinx("html", testroot="basic")
def test_directive_name(app: SphinxTestApp) -> None:
    app.build()
    page = soup(app, "sub/page")
    label = labels(app, "sub/page")[1]
    assert label["id"] == "named-label"
    # A label with an explicit target as well gets both IDs
    assert [span["id"] for span in label.select("span[id]")] == ["summary-label"]
    hrefs = [link["href"] for link in page.select("a.reference.internal")]
    assert hrefs == ["#named-label", "#summary-label"]


@pytest.mark.sphinx("html", testroot="basic")
def test_directive_text_markup(app: SphinxTestApp) -> None:
    app.build()
    label = labels(app, "sub/page")[2]
    text = one(label, ".eu-ai-label-text")
    assert text.get_text() == "Summary written carefully with help from"
    assert one(text, "em").get_text() == "carefully"
    assert one(text, "a")["href"] == "https://example.com/policy"
    # The basic icon still comes after the text
    children = [child for child in label.children if isinstance(child, Tag)]
    assert [child.name for child in children] == ["span", "img", "img"]


@pytest.mark.sphinx("text", testroot="basic")
def test_text_builder_fallback_keeps_markup(app: SphinxTestApp) -> None:
    app.build()
    output = (Path(app.outdir) / "sub" / "page.txt").read_text()
    assert "Summary written *carefully* with help from AI" in output


@pytest.mark.sphinx("gettext", testroot="i18n", srcdir="i18n-gettext")
def test_text_markup_extracted_for_translation(app: SphinxTestApp) -> None:
    app.build()
    assert 'msgid "See `our policy <https://example.com/policy>`_"' in (Path(app.outdir) / "index.pot").read_text()


@pytest.mark.sphinx("html", testroot="i18n")
def test_text_markup_translated(app: SphinxTestApp) -> None:
    app.build()
    text = one(labels(app)[1], ".eu-ai-label-text")
    assert text.get_text() == "Voir notre politique"
    assert one(text, "a")["href"] == "https://example.com/politique"
