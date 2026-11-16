"""Renderer-neutral dependency graph over an already authorized read view."""


def neutral_graph(records, venture=None):
    records = [r for r in records if venture is None or r["venture"] == venture]
    by_id = {r["id"]: r for r in records}
    return {"nodes": [{key: r[key] for key in ("id", "type", "parent", "status")}
                      for r in records],
            "edges": [{"from": dependency, "to": r["id"],
                       "blocking": by_id[dependency]["status"] != "done"}
                      for r in records for dependency in r["depends_on"] if dependency in by_id]}
