"""Sphinx extension for adding the European Commission's AI labelling icons to documentation."""

from __future__ import annotations

import shutil
from html import escape
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.errors import ConfigError
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util.nodes import split_explicit_title
from sphinx.util.osutil import relative_uri

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.util.typing import OptionSpec
    from sphinx.writers.html5 import HTML5Translator
    from sphinx.writers.latex import LaTeXTranslator

__version__ = version("sphinx-eu-ai-label")

logger = logging.getLogger(__name__)

KINDS = ("basic", "generated", "modified")
VARIANTS = ("auto", "black", "white", "black-50", "white-50")
ALIGNMENTS = ("left", "center", "right")
LATEX_ENVIRONMENTS = {"left": "flushleft", "center": "center", "right": "flushright"}

# What each icon says, used as its alt text. The generated and modified icons include their own wording, so
# they need no text label by default.
ALT_TEXTS = {
    "basic": "AI",
    "generated": "AI-generated",
    "modified": "AI-modified",
}

# Page metadata field that labels a page, and the value that opts a page out of eu_ai_label_page
PAGE_FIELD = "ai-label"
NO_PAGE_LABEL = "none"

STATIC_DIR = Path(__file__).parent / "_static"
# Kept out of STATIC_DIR so they aren't copied into HTML output
LATEX_ICONS_DIR = Path(__file__).parent / "latex" / "icons"
STATIC_PREFIX = "eu_ai_label"
CSS_FILE = f"{STATIC_PREFIX}/eu_ai_label.css"


def icon_path(kind: str, variant: str, ext: str = "svg") -> str:
    """Path of an icon, relative to the HTML output's ``_static`` directory or the LaTeX output directory.

    HTML uses the SVG icons. LaTeX uses PDF conversions of them, as pdflatex can't include SVG.
    """
    return f"{STATIC_PREFIX}/icons/{kind}-{variant}.{ext}"


class ai_label(nodes.General, nodes.Element):  # noqa: N801 - docutils node naming convention
    """A label, either block-level (from the directive) or inline (from the role).

    Its text, if any, is an ``ai_label_text`` child.
    """


class ai_label_text(nodes.Inline, nodes.TextElement):  # noqa: N801 - docutils node naming convention
    """A label's text.

    Text from the directive's ``:text:`` option is marked translatable, so Sphinx extracts and translates it like
    any paragraph, markup included. Text from config isn't, as it's set per language in ``conf.py``.

    This isn't a ``nodes.inline``, because Sphinx unwraps translatable ``inline`` nodes after translating them.
    """


def parse_spec(spec: str) -> tuple[str, str | None]:
    """Parse ``kind [variant]``, as used by the role and page labels."""
    kind, *rest = spec.split() or [""]
    if kind not in KINDS:
        raise ValueError(f"Unknown AI label kind {kind!r}; expected one of {', '.join(KINDS)}")
    if len(rest) > 1:
        raise ValueError(f"Expected an AI label kind and optional variant, not {spec!r}")
    variant = rest[0] if rest else None
    if variant is not None and variant not in VARIANTS:
        raise ValueError(f"Unknown AI label variant {variant!r}; expected one of {', '.join(VARIANTS)}")
    return kind, variant


def make_label(config: Config, kind: str, text: str | None, variant: str | None, inline: bool) -> ai_label:
    node = ai_label(
        kind=kind,
        alt=ALT_TEXTS[kind],
        variant=variant or config.eu_ai_label_variant,
        inline=inline,
    )
    if text is None:
        text = config.eu_ai_label_texts.get(kind, "")
    if text:
        node += ai_label_text(text, text)
    return node


class AILabelDirective(SphinxDirective):
    optional_arguments = 1
    has_content = False
    option_spec: OptionSpec = {  # noqa: RUF012 - docutils declares it as an instance attribute
        "text": directives.unchanged,
        "variant": lambda arg: directives.choice(arg, VARIANTS),
        "align": lambda arg: directives.choice(arg, ALIGNMENTS),
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        kind = self.arguments[0] if self.arguments else "basic"
        if kind not in KINDS:
            raise self.error(f"Unknown AI label kind {kind!r}; expected one of {', '.join(KINDS)}")
        text = self.options.get("text")
        # Text from the option is added below rather than by make_label, so it can contain markup such as links
        node = make_label(self.config, kind, None if text is None else "", self.options.get("variant"), inline=False)
        if text:
            text_node = ai_label_text(text, "", *self.parse_inline(text, lineno=self.lineno)[0], translatable=True)
            self.set_source_info(text_node)
            node += text_node
        node["align"] = self.options.get("align", "left")
        node["classes"] += self.options.get("class", [])
        self.add_name(node)
        self.set_source_info(node)
        return [node]


class AILabelRole(SphinxRole):
    """``:ai-label:`kind [variant]``` or ``:ai-label:`Text <kind [variant]>```."""

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        has_text, text, spec = split_explicit_title(self.text)
        try:
            kind, variant = parse_spec(spec)
        except ValueError as error:
            return self.problem(str(error))
        node = make_label(self.config, kind, text if has_text else None, variant, inline=True)
        self.set_source_info(node)
        return [node], []

    def problem(self, message: str) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        msg = self.inliner.reporter.error(message, line=self.lineno)
        return [self.inliner.problematic(self.rawtext, self.rawtext, msg)], [msg]


class AILabelFallback(SphinxPostTransform):
    """Replace labels with plain text for builders that can't show the icons."""

    default_priority = 200

    def run(self, **kwargs: Any) -> None:
        for node in list(self.document.findall(ai_label)):
            replacement_type = nodes.inline if node["inline"] else nodes.paragraph
            node.replace_self(replacement_type("", "", *fallback_content(node), classes=node["classes"]))


def fallback_content(node: ai_label) -> list[nodes.Node]:
    """The label without its icons, in the same order as the HTML output."""
    if not node.children:
        return [nodes.Text(node["alt"])]
    text = node.children[0].children
    if node["kind"] == "basic":
        return [*text, nodes.Text(f" {node['alt']}")]
    return list(text)


def label_icons_html(self: HTML5Translator, node: ai_label) -> str:
    builder = self.builder
    page_uri = builder.get_target_uri(builder.current_docname)
    size = builder.config.eu_ai_label_inline_size if node["inline"] else builder.config.eu_ai_label_size

    def img(variant: str, extra_class: str = "", hidden: bool = False) -> str:
        src = relative_uri(page_uri, f"_static/{icon_path(node['kind'], variant)}")
        classes = " ".join(filter(None, ["eu-ai-label-icon", extra_class]))
        hidden_attr = " hidden" if hidden else ""
        return (
            f'<img class="{classes}" src="{escape(src)}" alt="{escape(node["alt"])}" style="height: {escape(size)}"'
            f"{hidden_attr} />"
        )

    if node["variant"] == "auto":
        # The dark icon is hidden so only one shows without the stylesheet, which overrides this in dark mode
        return img("black", "eu-ai-label-icon-light") + img("white", "eu-ai-label-icon-dark", hidden=True)
    return img(node["variant"])


def label_tag(node: ai_label) -> str:
    return "span" if node["inline"] else "div"


def visit_ai_label_html(self: HTML5Translator, node: ai_label) -> None:
    classes = ["eu-ai-label", f"eu-ai-label-{node['kind']}"]
    if node["inline"]:
        classes.append("eu-ai-label-inline")
    else:
        classes += ["eu-ai-label-block", f"eu-ai-label-align-{node['align']}"]
    classes += node["classes"]

    # Only the first ID goes on the element, so cross-references to any others get empty spans as their targets
    id_attr = f' id="{escape(node["ids"][0])}"' if node["ids"] else ""
    extra_ids = "".join(f'<span id="{escape(id_)}"></span>' for id_ in node["ids"][1:])
    self.body.append(f'<{label_tag(node)}{id_attr} class="{escape(" ".join(classes))}">{extra_ids}')
    # The basic icon completes custom text such as "Summary generated with", so it goes last
    if node["kind"] != "basic":
        self.body.append(label_icons_html(self, node))


def depart_ai_label_html(self: HTML5Translator, node: ai_label) -> None:
    if node["kind"] == "basic":
        self.body.append(label_icons_html(self, node))
    self.body.append(f"</{label_tag(node)}>")


def visit_ai_label_text_html(self: HTML5Translator, node: ai_label_text) -> None:
    self.body.append('<span class="eu-ai-label-text">')


def depart_ai_label_text_html(self: HTML5Translator, node: ai_label_text) -> None:
    self.body.append("</span>")


def add_page_label(app: Sphinx, doctree: nodes.document) -> None:
    """Label the page from its metadata, or from ``eu_ai_label_page``, at the top of the page."""
    env = app.env
    spec = str(env.metadata[env.docname].get(PAGE_FIELD, app.config.eu_ai_label_page) or "")
    if not spec or spec == NO_PAGE_LABEL:
        return
    try:
        kind, variant = parse_spec(spec)
    except ValueError as error:
        logger.warning(f"{error} in the page's {PAGE_FIELD!r} metadata", location=env.docname)
        return
    label = make_label(app.config, kind, None, variant, inline=False)
    label["align"] = "left"

    # Under the page's title if it starts with one, so the label is visible as soon as the content is
    first = next((child for child in doctree.children if not isinstance(child, nodes.Invisible)), None)
    if isinstance(first, nodes.section) and first.children and isinstance(first[0], nodes.title):
        first.insert(1, label)
    else:
        doctree.insert(doctree.index(first) if first is not None else len(doctree.children), label)


def label_icon_latex(self: LaTeXTranslator, node: ai_label) -> str:
    config = self.config
    size = config.eu_ai_label_latex_inline_size if node["inline"] else config.eu_ai_label_latex_size
    # Print has no dark mode
    variant = "black" if node["variant"] == "auto" else node["variant"]
    base = icon_path(node["kind"], variant, ext="pdf").removesuffix(".pdf")
    # Braces around the base name, as Sphinx does for images, so dots and other characters in it are safe
    # The icons have wide margins, so centre them on the text (around 0.5ex up) rather than on the baseline
    return rf"\raisebox{{\dimexpr 0.5ex - 0.5\height\relax}}{{\sphinxincludegraphics[height={size}]{{{{{base}}}.pdf}}}}"


def preceding_target_ids(node: ai_label) -> set[str]:
    """IDs of the targets just before a label, which Sphinx writes itself."""
    ids: set[str] = set()
    sibling = node.previous_sibling()
    while isinstance(sibling, nodes.target):
        ids.update(sibling["ids"], [sibling["refid"]] if "refid" in sibling else [])
        sibling = sibling.previous_sibling()
    return ids


def visit_ai_label_latex(self: LaTeXTranslator, node: ai_label) -> None:
    if not node["inline"]:
        self.body.append(f"\n\\begin{{{LATEX_ENVIRONMENTS[node['align']]}}}\n")
    # Targets for cross-references, such as from the directive's :name:. Sphinx already writes those for any
    # explicit targets just before the label, and writing them again would make LaTeX warn about duplicates.
    if ids := [id_ for id_ in node["ids"] if id_ not in preceding_target_ids(node)]:
        self.body.append(r"\phantomsection" + "".join(self.hypertarget(id_, anchor=False) for id_ in ids))
    # The basic icon completes custom text such as "Summary generated with", so it goes last
    if node["kind"] != "basic":
        self.body.append(label_icon_latex(self, node))
        if node.children:
            self.body.append("~")


def depart_ai_label_latex(self: LaTeXTranslator, node: ai_label) -> None:
    if node["kind"] == "basic":
        if node.children:
            self.body.append("~")
        self.body.append(label_icon_latex(self, node))
    if not node["inline"]:
        self.body.append(f"\n\\end{{{LATEX_ENVIRONMENTS[node['align']]}}}\n")


def visit_ai_label_text_latex(self: LaTeXTranslator, node: ai_label_text) -> None:
    pass  # The text's children, including any markup, are written as usual


def depart_ai_label_text_latex(self: LaTeXTranslator, node: ai_label_text) -> None:
    pass


def copy_latex_icons(app: Sphinx, exception: Exception | None) -> None:
    if app.builder.format != "latex":
        return
    destination = Path(app.outdir) / STATIC_PREFIX / "icons"
    destination.mkdir(parents=True, exist_ok=True)
    for icon in LATEX_ICONS_DIR.glob("*.pdf"):
        shutil.copyfile(icon, destination / icon.name)


def check_config(app: Sphinx, config: Config) -> None:
    if config.eu_ai_label_variant not in VARIANTS:
        raise ConfigError(
            f"eu_ai_label_variant must be one of {', '.join(VARIANTS)}, not {config.eu_ai_label_variant!r}"
        )
    if unknown := set(config.eu_ai_label_texts) - set(KINDS):
        raise ConfigError(f"eu_ai_label_texts has unknown kinds: {', '.join(sorted(unknown))}")
    if config.eu_ai_label_page is not None:
        try:
            parse_spec(config.eu_ai_label_page)
        except ValueError as error:
            raise ConfigError(f"eu_ai_label_page: {error}") from None
    config.html_static_path.append(str(STATIC_DIR))


def add_fallback(app: Sphinx) -> None:
    # The gettext builder needs the labels intact to extract their text
    if app.builder.format not in {"html", "latex"} and app.builder.name != "gettext":
        app.add_post_transform(AILabelFallback)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("eu_ai_label_variant", "auto", "env", types=frozenset({str}))
    app.add_config_value("eu_ai_label_size", "2.5em", "html", types=frozenset({str}))
    app.add_config_value("eu_ai_label_inline_size", "1.75em", "html", types=frozenset({str}))
    app.add_config_value("eu_ai_label_texts", {}, "env", types=frozenset({dict}))
    app.add_config_value("eu_ai_label_page", None, "env", types=frozenset({str, type(None)}))
    # Separate from the HTML sizes, as CSS lengths such as rem aren't valid in LaTeX
    app.add_config_value("eu_ai_label_latex_size", "2.5em", "", types=frozenset({str}))
    app.add_config_value("eu_ai_label_latex_inline_size", "1.75em", "", types=frozenset({str}))
    app.connect("config-inited", check_config)

    app.add_node(
        ai_label,
        html=(visit_ai_label_html, depart_ai_label_html),
        latex=(visit_ai_label_latex, depart_ai_label_latex),
    )
    app.add_node(
        ai_label_text,
        html=(visit_ai_label_text_html, depart_ai_label_text_html),
        latex=(visit_ai_label_text_latex, depart_ai_label_text_latex),
    )
    app.add_directive("ai-label", AILabelDirective)
    app.add_role("ai-label", AILabelRole())
    app.connect("builder-inited", add_fallback)
    app.connect("build-finished", copy_latex_icons)
    # After Sphinx's metadata collector, which runs at the default priority
    app.connect("doctree-read", add_page_label, priority=600)
    app.add_css_file(CSS_FILE)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
