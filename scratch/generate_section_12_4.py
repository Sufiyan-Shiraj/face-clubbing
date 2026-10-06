import json
from pathlib import Path
from collections import defaultdict

def generate_section_12_4():
    sug_path = Path("suggestions.json")
    if not sug_path.exists():
        sug_path = Path("export/.cache/suggestions.json")
    people_path = Path("export/people.json")

    with open(sug_path, "r", encoding="utf-8") as f:
        sug_data = json.load(f)
    with open(people_path, "r", encoding="utf-8") as f:
        people_data = json.load(f)

    people_by_id = {p["id"]: p for p in people_data["people"]}
    groups = sug_data["maybe_groups"]

    seen_clusters = set()
    total_links = 0
    table_rows = []

    for g in groups:
        gid = g["group_id"]
        clusters = g["clusters"]
        cluster_cnt = g["cluster_count"]
        links = g["links"]
        total_links += len(links)

        # Assertion: cluster_count equals len(clusters)
        assert cluster_cnt == len(clusters), f"Group {gid} cluster_count mismatch"

        # Assertion: no cluster is in two groups
        for c in clusters:
            assert c not in seen_clusters, f"Cluster {c} appears in multiple groups"
            seen_clusters.add(c)

        # Assertion: each group's photos_count equals the union of its members' photo_ids
        union_pids = set()
        for c in clusters:
            assert c in people_by_id, f"Cluster {c} not found in people.json"
            union_pids.update(people_by_id[c]["photo_ids"])
        assert g["photos_count"] == len(union_pids), (
            f"Group {gid} photos_count mismatch: json has {g['photos_count']} but union is {len(union_pids)}"
        )

        adj = defaultdict(set)
        link_strs = []
        for l in links:
            ca = l["cluster_a"]
            cb = l["cluster_b"]
            dist = l["distance"]
            assert ca in clusters and cb in clusters, f"Link {ca}-{cb} not in group clusters"
            adj[ca].add(cb)
            adj[cb].add(ca)
            link_strs.append(f"`({ca}, {cb}): {dist:.4f}`")

        # Connectivity assertion (BFS)
        if len(clusters) > 1:
            visited = set()
            queue = [clusters[0]]
            visited.add(clusters[0])
            while queue:
                curr = queue.pop(0)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            assert visited == set(clusters), f"Group {gid} is not connected: visited {visited} vs {clusters}"

        clusters_str = ", ".join(f"`{c}`" for c in clusters)
        links_formatted = ", ".join(link_strs)
        table_rows.append(
            f"| **Group {gid}** | {clusters_str} | {cluster_cnt} | {len(union_pids)} | {links_formatted} |"
        )

    table_md = "\n".join([
        "| Group ID | Constituent Cluster IDs | Cluster Count | Combined Photos Count | Pairwise Links & Distances |",
        "| :---: | :--- | :---: | :---: | :--- |",
        *table_rows
    ])

    print("All assertions PASSED successfully!")
    print(f"Total Groups: {len(groups)}, Total Links: {total_links}")
    return table_md

if __name__ == "__main__":
    md = generate_section_12_4()
    with open("scratch/section_12_4_table.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Saved to scratch/section_12_4_table.md")
