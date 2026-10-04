"""Sphinx extension for adding the European Commission's AI labelling icons to documentation."""

from __future__ import annotations

from html import escape
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.errors import ConfigError
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util.nodes import split_explicit_title
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


class ai_label(nodes.General, nodes.Element, addnodes.translatable):  # noqa: N801 - docutils node naming convention
    """A label, either block-level (from the directive) or inline (from the role).

    Text given in the directive's ``:text:`` option is kept in ``rawtext`` so it can be translated. Text from config
    isn't, as it's set per language in ``conf.py``.
    """

    def preserve_original_messages(self) -> None:
        pass  # The directive stores rawtext when it creates the node

    def apply_translated_message(self, original_message: str, translated_message: str) -> None:
        self["text"] = translated_message  # A label has at most one message, so it must be this one

    def extract_original_messages(self) -> list[str]:
        return [self["rawtext"]] if self.get("rawtext") else []


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
        "name": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        kind = self.arguments[0] if self.arguments else "basic"
        if kind not in KINDS:
            raise self.error(f"Unknown AI label kind {kind!r}; expected one of {', '.join(KINDS)}")
        node = make_label(self.config, kind, self.options.get("text"), self.options.get("variant"), inline=False)
        if "text" in self.options:
            node["rawtext"] = self.options["text"]
        node["align"] = self.options.get("align", "left")
        node["classes"] += self.options.get("class", [])
        self.add_name(node)
        self.set_source_info(node)
        return [node]


class AILabelRole(SphinxRole):
    """``:ai-label:`kind [variant]``` or ``:ai-label:`Text <kind [variant]>```."""

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        has_text, text, spec = split_explicit_title(self.text)
        kind, *rest = spec.split() or [""]
        if kind not in KINDS:
            return self.problem(f"Unknown AI label kind {kind!r}; expected one of {', '.join(KINDS)}")
        if len(rest) > 1:
            return self.problem(f"Expected an AI label kind and optional variant, not {spec!r}")
        variant = rest[0] if rest else None
        if variant is not None and variant not in VARIANTS:
            return self.problem(f"Unknown AI label variant {variant!r}; expected one of {', '.join(VARIANTS)}")
        node = make_label(self.config, kind, text if has_text else None, variant, inline=True)
        self.set_source_info(node)
        return [node], []

    def problem(self, message: str) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        msg = self.inliner.reporter.error(message, line=self.lineno)
        return [self.inliner.problematic(self.rawtext, self.rawtext, msg)], [msg]


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
        icons = img("black", "eu-ai-label-icon-light") + img("white", "eu-ai-label-icon-dark", hidden=True)
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

    # Only the first ID goes on the element, so cross-references to any others get empty spans as their targets
    id_attr = f' id="{escape(node["ids"][0])}"' if node["ids"] else ""
    extra_ids = "".join(f'<span id="{escape(id_)}"></span>' for id_ in node["ids"][1:])
    self.body.append(f'<{tag}{id_attr} class="{escape(" ".join(classes))}">{extra_ids}{content}</{tag}>')
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
    # The gettext builder needs the labels intact to extract their text
    if app.builder.format != "html" and app.builder.name != "gettext":
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
