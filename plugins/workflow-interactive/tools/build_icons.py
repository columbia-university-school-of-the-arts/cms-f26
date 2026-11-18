"""Instructor tool: rebuild references/icons.js from the pinned icon packages.

Run from the hub root: python3 plugins/workflow-interactive/tools/build_icons.py
Downloads two npm tarballs (no npm needed), keeps only the icons listed below,
and writes them as one JavaScript object the page embeds. Students never run it.
"""
import io, json, pathlib, re, tarfile, urllib.request

SIMPLE_ICONS = "16.36.0"  # CC0-1.0
LUCIDE = "1.66.0"         # ISC

BRANDS = [
    "themoviedatabase", "youtube", "vimeo", "internetarchive", "zotero", "wikipedia",
    "googledrive", "github", "imdb", "letterboxd", "spotify", "soundcloud", "reddit",
    "instagram", "tiktok", "x", "arxiv", "googlescholar", "wikidata",
    "notion", "obsidian", "dropbox", "googledocs", "googlesheets", "bluesky", "mastodon",
    "twitch", "flickr", "bandcamp", "archiveofourown", "substack", "medium", "tumblr",
    "applepodcasts", "orcid", "researchgate", "academia", "semanticscholar", "kaggle",
]
GENERIC = [
    "film", "globe", "mic", "database", "file-text", "folder", "tag", "book-open",
    "pen-line", "git-compare", "download", "search", "camera", "chart-column", "user",
    "sparkles", "cog", "scissors", "message-square", "image", "music", "upload",
    "list-checks", "quote", "map", "calendar", "link", "archive", "clapperboard",
    "newspaper", "star", "check", "x", "triangle-alert", "play", "pause", "skip-forward",
    "git-commit-horizontal", "arrow-up-from-line", "arrow-down-to-line", "copy", "plus",
    "users", "bot", "library", "notebook-pen", "video", "tv", "headphones", "layers",
    "filter", "shuffle", "eye", "lightbulb", "send", "inbox", "table", "workflow",
]

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = HERE / "skills" / "interactive-map" / "references" / "icons.js"


def tarball(name, version):
    url = f"https://registry.npmjs.org/{name}/-/{name}-{version}.tgz"
    with urllib.request.urlopen(url) as r:
        return tarfile.open(fileobj=io.BytesIO(r.read()), mode="r:gz")


def member(tar, path):
    f = tar.extractfile(f"package/{path}")
    return f.read().decode() if f else None


def main():
    si = tarball("simple-icons", SIMPLE_ICONS)
    data = {d["slug"]: d for d in json.loads(member(si, "data/simple-icons.json"))}
    brand, missing = {}, []
    for slug in BRANDS:
        try:
            svg = member(si, f"icons/{slug}.svg")
        except KeyError:
            missing.append(slug)
            continue
        path = re.search(r'<path d="([^"]+)"', svg).group(1)
        brand[slug] = {"path": path, "color": "#" + data[slug]["hex"], "title": data[slug]["title"]}
    lu = tarball("lucide-static", LUCIDE)
    generic = {}
    for name in GENERIC:
        svg = member(lu, f"icons/{name}.svg")
        inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
        generic[name] = {"svg": re.sub(r"\s+", " ", inner).strip()}
    body = json.dumps({"brand": brand, "generic": generic,
                       "versions": {"simple-icons": SIMPLE_ICONS, "lucide-static": LUCIDE}},
                      separators=(",", ":"), sort_keys=True)
    OUT.write_text(
        "/* Icons: Simple Icons " + SIMPLE_ICONS + " (CC0-1.0), brand marks belong to their owners;\n"
        "   Lucide " + LUCIDE + " (ISC). Built by tools/build_icons.py. */\n"
        "var WF_ICONS = " + body + ";\n")
    print(f"{len(brand)} brands, {len(generic)} generic; missing brands: {missing or 'none'}")


if __name__ == "__main__":
    main()
