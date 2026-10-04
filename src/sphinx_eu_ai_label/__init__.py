"""Sphinx extension for adding the European Commission's AI labelling icons to documentation."""

from __future__ import annotations

from html import escape
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.errors import ConfigError
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util.osutil import relative_uri

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.util.typing import OptionSpec
    from sphinx.writers.html5 import HTML5Translator

__version__ = version("sphinx-eu-ai-label")

KINDS = ("basic", "generated", "modified")
VARIANTS = ("auto", "black", "white", "black-50", "white-50")
ALIGNMENTS = ("left", "center", "right")

# What each icon says, used as its alt text. The generated and modified icons include their own wording, so
# they need no text label by default.
ALT_TEXTS = {
    "basic": "AI",
    "generated": "AI-generated",
    "modified": "AI-modified",
}

STATIC_DIR = Path(__file__).parent / "_static"
STATIC_PREFIX = "eu_ai_label"
CSS_FILE = f"{STATIC_PREFIX}/eu_ai_label.css"


def icon_path(kind: str, variant: str) -> str:
    """Path of an icon, relative to the HTML output's ``_static`` directory."""
    return f"{STATIC_PREFIX}/icons/{kind}-{variant}.svg"


class ai_label(nodes.General, nodes.Element):  # noqa: N801 - docutils node naming convention
    """A label, either block-level (from the directive) or inline (from the role)."""


def make_label(config: Config, kind: str, text: str | None, variant: str | None, inline: bool) -> ai_label:
    if text is None:
        text = config.eu_ai_label_texts.get(kind, "")
    return ai_label(
        kind=kind,
        text=text,
        alt=ALT_TEXTS[kind],
        variant=variant or config.eu_ai_label_variant,
        inline=inline,
    )


class AILabelDirective(SphinxDirective):
    optional_arguments = 1
    has_content = False
    option_spec: OptionSpec = {  # noqa: RUF012 - docutils declares it as an instance attribute
        "text": directives.unchanged,
        "variant": lambda arg: directives.choice(arg, VARIANTS),
        "align": lambda arg: directives.choice(arg, ALIGNMENTS),
        "class": directives.class_option,
    }

    def run(self) -> list[nodes.Node]:
        kind = self.arguments[0] if self.arguments else "basic"
        if kind not in KINDS:
            raise self.error(f"Unknown AI label kind {kind!r}; expected one of {', '.join(KINDS)}")
        node = make_label(self.config, kind, self.options.get("text"), self.options.get("variant"), inline=False)
        node["align"] = self.options.get("align", "left")
        node["classes"] += self.options.get("class", [])
        self.set_source_info(node)
        return [node]


class AILabelRole(SphinxRole):
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        kind = self.text.strip()
        if kind not in KINDS:
            msg = self.inliner.reporter.error(
                f"Unknown AI label kind {kind!r}; expected one of {', '.join(KINDS)}", line=self.lineno
            )
            return [self.inliner.problematic(self.rawtext, self.rawtext, msg)], [msg]
        node = make_label(self.config, kind, None, None, inline=True)
        self.set_source_info(node)
        return [node], []


class AILabelFallback(SphinxPostTransform):
    """Replace labels with plain text for non-HTML builders, which can't show the icons."""

    default_priority = 200

    def run(self, **kwargs: Any) -> None:
        for node in list(self.document.findall(ai_label)):
            replacement_type = nodes.inline if node["inline"] else nodes.paragraph
            node.replace_self(replacement_type("", plain_text(node), classes=node["classes"]))


def plain_text(node: ai_label) -> str:
    """The label as text, in the same order as the HTML output."""
    if not node["text"]:
        return node["alt"]
    if node["kind"] == "basic":
        return f"{node['text']} {node['alt']}"
    return node["text"]


def visit_ai_label_html(self: HTML5Translator, node: ai_label) -> None:
    builder = self.builder
    page_uri = builder.get_target_uri(builder.current_docname)
    size = builder.config.eu_ai_label_inline_size if node["inline"] else builder.config.eu_ai_label_size

    def img(variant: str, extra_class: str = "") -> str:
        src = relative_uri(page_uri, f"_static/{icon_path(node['kind'], variant)}")
        classes = " ".join(filter(None, ["eu-ai-label-icon", extra_class]))
        return (
            f'<img class="{classes}" src="{escape(src)}" alt="{escape(node["alt"])}" style="height: {escape(size)}" />'
        )

    if node["variant"] == "auto":
        icons = img("black", "eu-ai-label-icon-light") + img("white", "eu-ai-label-icon-dark")
    else:
        icons = img(node["variant"])

    text = f'<span class="eu-ai-label-text">{escape(node["text"])}</span>' if node["text"] else ""
    # The basic icon completes custom text such as "Summary generated with", so it goes last
    content = text + icons if node["kind"] == "basic" else icons + text

    classes = ["eu-ai-label", f"eu-ai-label-{node['kind']}"]
    if node["inline"]:
        tag = "span"
        classes.append("eu-ai-label-inline")
    else:
        tag = "div"
        classes += ["eu-ai-label-block", f"eu-ai-label-align-{node['align']}"]
    classes += node["classes"]

    self.body.append(f'<{tag} class="{escape(" ".join(classes))}">{content}</{tag}>')
    raise nodes.SkipNode


def check_config(app: Sphinx, config: Config) -> None:
    if config.eu_ai_label_variant not in VARIANTS:
        raise ConfigError(
            f"eu_ai_label_variant must be one of {', '.join(VARIANTS)}, not {config.eu_ai_label_variant!r}"
        )
    if unknown := set(config.eu_ai_label_texts) - set(KINDS):
        raise ConfigError(f"eu_ai_label_texts has unknown kinds: {', '.join(sorted(unknown))}")
    config.html_static_path.append(str(STATIC_DIR))


def add_fallback(app: Sphinx) -> None:
    if app.builder.format != "html":
        app.add_post_transform(AILabelFallback)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("eu_ai_label_variant", "auto", "env", types=frozenset({str}))
    app.add_config_value("eu_ai_label_size", "2.5em", "html", types=frozenset({str}))
    app.add_config_value("eu_ai_label_inline_size", "1.75em", "html", types=frozenset({str}))
    app.add_config_value("eu_ai_label_texts", {}, "env", types=frozenset({dict}))
    app.connect("config-inited", check_config)

    app.add_node(ai_label, html=(visit_ai_label_html, None))
    app.add_directive("ai-label", AILabelDirective)
    app.add_role("ai-label", AILabelRole())
    app.connect("builder-inited", add_fallback)
    app.add_css_file(CSS_FILE)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
