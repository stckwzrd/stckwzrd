#!/usr/bin/env python3
"""Rebuild the stats block of README.md from the GitHub API (no WakaTime).

Only aggregates are written (language shares, counts); private repository
names never reach the README. Needs a token that can read your repos:
GH_TOKEN env var (in Actions: the GH_TOKEN secret).
"""
import json, os, re, sys, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!--START_SECTION:stats-->", "<!--END_SECTION:stats-->"
BAR = 22
TOP = 7

QUERY = """
query {
  viewer {
    login
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        isPrivate
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
    publicRepos: repositories(ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount }
    privateRepos: repositories(ownerAffiliations: OWNER, privacy: PRIVATE) { totalCount }
  }
}
"""


def graphql(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["viewer"]


def bar(share):
    full = round(share * BAR)
    return "[" + "#" * full + "." * (BAR - full) + "]"


def render(v):
    langs = Counter()
    for repo in v["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
    total = sum(langs.values()) or 1
    top = langs.most_common(TOP)
    rest = total - sum(n for _, n in top)
    if rest > 0:
        top.append(("Other", rest))

    name_w = max(len(n) for n, _ in top)
    biggest = top[0][1]
    rows_txt = [f" {n:<{name_w}}  {bar(size / biggest)}  {size / total * 100:5.1f}% " for n, size in top]
    inner = max(len(r) for r in rows_txt)
    title = "─[ Language distribution ]"
    lines = ["┌" + title + "─" * (inner - len(title)) + "┐"]
    lines += [f"│{r:<{inner}}│" for r in rows_txt]
    lines.append("└" + "─" * inner + "┘")
    langs_block = "\n".join(lines)

    c = v["contributionsCollection"]
    rows = [
        ("Contributions", f"{c['contributionCalendar']['totalContributions']:,}", "last 12 months"),
        ("Repositories", f"{v['publicRepos']['totalCount'] + v['privateRepos']['totalCount']}",
         f"{v['publicRepos']['totalCount']} public / {v['privateRepos']['totalCount']} private"),
        ("Languages", f"{len(langs)}", f"{total / 1e6:.1f} MB of source analysed"),
        ("Primary language", top[0][0], f"{top[0][1] / total * 100:.0f}% of all code"),
    ]
    table = "| Metric | Value | Note |\n|:--|--:|:--|\n" + "\n".join(
        f"| {a} | **{b}** | {d} |" for a, b, d in rows
    )
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (
        f"```text\n{langs_block}\n```\n\n"
        f"{table}\n\n"
        f"<sub>Generated from the GitHub API, last updated {stamp}.</sub>"
    )


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("set GH_TOKEN")
    block = render(graphql(token))
    text = README.read_text()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit("markers not found in README.md")
    README.write_text(pattern.sub(lambda _: f"{START}\n{block}\n{END}", text))
    print("README stats updated")


if __name__ == "__main__":
    main()
