from dataclasses import dataclass
from html.parser import HTMLParser

import requests


@dataclass(frozen=True)
class WikiSource:
    title: str
    url: str
    text: str


class _WikiTextParser(HTMLParser):
    _TEXT_TAGS = {"p", "li", "figcaption", "th", "td"}

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._current: list[str] = []
        self._active_tag: str | None = None
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "sup"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self._TEXT_TAGS and self._active_tag is None:
            self._active_tag = tag
            self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "sup"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == self._active_tag:
            block = " ".join("".join(self._current).split())
            if block:
                self.blocks.append(block)
            self._current = []
            self._active_tag = None

    def handle_data(self, data: str) -> None:
        if self._active_tag and not self._skip_depth:
            self._current.append(data)


def load_wiki_source(url: str, title: str) -> WikiSource:
    response = requests.get(
        url,
        headers={"User-Agent": "haystack-rag-demo/0.1 (educational project)"},
        timeout=30,
    )
    response.raise_for_status()

    parser = _WikiTextParser()
    parser.feed(response.text)

    text = "\n\n".join(_dedupe_blocks(parser.blocks))
    if not text:
        raise RuntimeError("Wiki page did not contain extractable article text")

    return WikiSource(title=title, url=url, text=text)


def _dedupe_blocks(blocks: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for block in blocks:
        normalized = block.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(block)
    return deduped
