import os
import requests

TOKEN=os.getenv("GH_TOKEN")
USERNAME="PARSA313-CLOUD"

query="""
query($username: String!) {
  user(login: $username) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      restrictedContributionsCount
    }
  }
}
"""

headers={"Authorization": f"bearer {TOKEN}"}
res=requests.post("https://api.github.com/graphql", json={"query": query, "variables": {"username": USERNAME}}, headers=headers)
data=res.json()["data"]["user"]

repos_count=data["repositories"]["totalCount"]
contribs=data["contributionsCollection"]

commits=contribs["totalCommitContributions"]
prs=contribs["totalPullRequestContributions"]
reviews=contribs["totalPullRequestReviewContributions"]
total_contribs=commits+prs+reviews+contribs["restrictedContributionsCount"]

lang_stats={}
for repo in data["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        l_name=edge["node"]["name"]
        l_color=edge["node"]["color"] or "#858585"
        l_size=edge["size"]
        if l_name not in lang_stats:
            lang_stats[l_name]={"size": 0, "color": l_color}
        lang_stats[l_name]["size"]+=l_size

total_size=sum(l["size"] for l in lang_stats.values()) or 1
sorted_langs=sorted(lang_stats.items(), key=lambda x: x[1]["size"], reverse=True)[:3]

lang_bars=""
lang_labels=""
current_x=48.0
total_bar_width=704.0

label_positions=[48.0, 282.66, 517.33]

for idx, (l_name, l_info) in enumerate(sorted_langs):
    pct=l_info["size"]/total_size
    width=pct*total_bar_width
    lang_bars+=f'<rect x="{current_x}" y="254" width="{width}" height="6" rx="3" fill="{l_info["color"]}"/>\n'
    current_x+=width
    
    pct_str=f"{int(round(pct*100))}%"
    lx=label_positions[idx] if idx<len(label_positions) else 48.0
    lang_labels+=f'''<g>
        <rect x="{lx}" y="279" width="8" height="8" rx="2" fill="{l_info["color"]}"/>
        <text x="{lx+16}" y="286" fill="#a5a5b3" font-family="ui-monospace, monospace" font-size="10" letter-spacing="1.4">{l_name.upper()} {pct_str}</text>
    </g>\n'''

with open("stats.template.svg", "r", encoding="utf-8") as f:
    template=f.read()

output=template.format(
    TOTAL_CONTRIBUTIONS=total_contribs,
    REPOS_COUNT=repos_count,
    COMMITS_COUNT=commits,
    PRS_COUNT=prs,
    REVIEWS_COUNT=reviews,
    LANG_BARS=lang_bars,
    LANG_LABELS=lang_labels
)

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(output)
