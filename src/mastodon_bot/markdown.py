import mistune
from mistune.renderers.rst import RSTRenderer
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html


class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            lexer = get_lexer_by_name(info, stripall=True)
            formatter = html.HtmlFormatter()
            return highlight(code, lexer, formatter)
        return '<pre><code>' + mistune.escape(code) + '</code></pre>'

    # def paragraph(self, text):
    #     text = text.replace('\n', '<br>')
    #     return f"<p>{text}</p>"


def to_html(markdown_text: str) -> str:
    markdown = mistune.create_markdown(
        renderer=HighlightRenderer(), escape=False, hard_wrap=True)
    return markdown(markdown_text)


def to_text(markdown_text: str) -> str:
    markdown = mistune.create_markdown(renderer=RSTRenderer(), escape=False)
    return markdown(markdown_text)
