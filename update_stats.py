import os
import requests

TOKEN=os.environ.get("GH_TOKEN")
USERNAME="PARSA313-CLOUD"

query="""
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: [OWNER, COLLABORATOR], isFork: false) {
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
      contributionCalendar {
        totalContributions
      }
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

headers={"Authorization": f"Bearer {TOKEN}"}
response=requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"login": USERNAME}},
    headers=headers
)

data=response.json().get("data", {}).get("user", {})
if not data:
    raise Exception(f"GraphQL Query Failed: {response.text}")

repos_count=data["repositories"]["totalCount"]
contribs_coll=data["contributionsCollection"]
commits_count=contribs_coll["totalCommitContributions"]

total_contribs=(
    contribs_coll["contributionCalendar"]["totalContributions"]
    + contribs_coll.get("restrictedContributionsCount", 0)
)

lang_sizes={}
lang_colors={}

for repo in data["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name=edge["node"]["name"]
        color=edge["node"]["color"] or "#bf03b9"
        size=edge["size"]
        lang_sizes[name]=lang_sizes.get(name, 0)+size
        lang_colors[name]=color

total_size=sum(lang_sizes.values())
sorted_langs=sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:3]

total_bar_width=704
start_x=48
bars_svg=[]
labels_svg=[]

current_x=start_x
label_x=48

for name, size in sorted_langs:
    pct=size/total_size if total_size>0 else 0
    width=pct*total_bar_width
    color=lang_colors[name]
    pct_formatted=f"{pct*100:.1f}%"
    
    bars_svg.append(f'<rect x="{current_x:.1f}" y="254" width="{width:.1f}" height="6" fill="{color}"/>')
    current_x+=width
    
    labels_svg.append(
        f'<g transform="translate({label_x:.1f} 280)">'
        f'<circle cx="4" cy="0" r="4" fill="{color}"/>'
        f'<text x="14" y="3" fill="#a5a5b3" font-family=\'"Inter", system-ui, sans-serif\' font-size="11">{name}</text>'
        f'<text x="{14 + len(name)*7 + 8}" y="3" fill="#a5a5b3" font-family=\'"Inter", system-ui, sans-serif\' font-size="11" opacity="0.6">{pct_formatted}</text>'
        f'</g>'
    )
    label_x+=140

with open("stats.template.svg", "r", encoding="utf-8") as f:
    svg_template=f.read()

output_svg=(
    svg_template
    .replace("{TOTAL_CONTRIBUTIONS}", f"{total_contribs:,}")
    .replace("{REPOS_COUNT}", str(repos_count))
    .replace("{COMMITS_COUNT}", f"{commits_count:,}")
    .replace("{LANG_BARS}", "\n    ".join(bars_svg))
    .replace("{LANG_LABELS}", "\n    ".join(labels_svg))
)

with open("gh-stats.svg", "w", encoding="utf-8") as f:
    f.write(output_svg)

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(output_svg)
