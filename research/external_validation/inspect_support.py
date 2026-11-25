"""Inspect offline evidence without reporting physical responses or policy outcomes."""

import argparse
import ast
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlopen

import networkx as nx
import pandas as pd


ROOT = Path(__file__).resolve().parent
META = ("timestamp", "config", "counter", "flag", "intervention")
GRAPH_MEMBER = "causalchamber/ground_truth/main.py"
CONFIG_TABLES = {
    "lt_validate_v1": "lt_validation_configs.csv",
    "wt_validate_v1": "wt_standard_validation_configs.csv",
    "wt_pc_validate_v1": "wt_pc_validation_configs.csv",
}
LEVELS = {
    "lt_interventions_standard_v1": {
        "uniform_reference": ["pol_1", "pol_2", "red"],
        "uniform_pol_1_mid": ["pol_1"],
        "uniform_pol_1_strong": ["pol_1"],
        "uniform_pol_2_mid": ["pol_2"],
        "uniform_pol_2_strong": ["pol_2"],
        "uniform_red_mid": ["red"],
        "uniform_red_strong": ["red"],
    },
    "lt_malus_v1": {"*": ["pol_1", "pol_2", "red", "green", "blue"]},
    "lt_spice_v1": {"*": ["green", "sps_current_ls", "offset_current_ls", "slope_f2", "slope_f3"]},
    "wt_bernoulli_v1": {"*": ["load_in", "load_out", "hatch"]},
    "wt_pressure_control_v1": {"hatch_0": ["hatch"]},
}


def file_record(path):
    with path.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
        stream.seek(0)
        md5 = hashlib.file_digest(stream, "md5").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": sha, "md5": md5}


def retrieve(entry, folder, download):
    path = folder / entry["file"]
    if not path.exists() and download:
        # Keep failed transfers from replacing an existing verified artifact.
        temporary = path.with_suffix(path.suffix + ".part")
        with urlopen(entry["url"], timeout=120) as source, temporary.open("wb") as dest:
            while chunk := source.read(1024 * 1024):
                dest.write(chunk)
        if file_record(temporary)["sha256"] != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {path.name}")
        temporary.replace(path)
    actual = file_record(path)
    for key in ("sha256", "md5", "bytes"):
        if key in entry and entry[key] != actual[key]:
            raise ValueError(f"{key} mismatch: {path.name}")
    return path, actual


def load_mk1_graphs(wheel):
    with zipfile.ZipFile(wheel) as archive:
        source = archive.read(GRAPH_MEMBER)
    # Read literal lists from the pinned wheel. Never import its remote lab client.
    values = {}
    prefixes = ("_edges_", "_variables_")
    for statement in ast.parse(source).body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        name = statement.targets[0]
        if not isinstance(name, ast.Name) or not name.id.startswith(prefixes):
            continue
        value = statement.value
        if isinstance(value, ast.Name):
            values[name.id] = values[value.id]
        elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            values[name.id] = values[value.left.id] + ast.literal_eval(value.right)
        else:
            values[name.id] = ast.literal_eval(value)
    graphs = {}
    for name in ("lt_standard", "wt_standard", "wt_pressure_control"):
        nodes, edges = values[f"_variables_{name}"], values[f"_edges_{name}"]
        if {node for edge in edges for node in edge} - set(nodes):
            raise ValueError(f"Unknown node in {name}")
        graph = nx.DiGraph()
        graph.add_nodes_from(nodes)
        graph.add_edges_from(edges)
        graphs[name] = graph
    return graphs


def linked_leds_figure():
    """Expand grouped nodes in linked_leds v1.0 Figure 1, with equations 1–2."""
    graph = nx.DiGraph()

    def edges(sources, targets):
        graph.add_edges_from((src, dst) for src in sources for dst in targets)

    def analog(name):
        outputs = [name, f"{name}_raw"]
        edges([f"{prefix}_{name}" for prefix in ("offset", "res", "sps")], outputs)
        return outputs

    edges(["red", "green", "blue"], analog("current_ls")
          + [f"{channel}_{i}" for i in (1, 2, 3) for channel in ("ir", "vis")])
    for i in (1, 2, 3):
        for channel in ("ir", "vis"):
            sensor = f"{channel}_{i}"
            edges([f"t_{sensor}", f"diode_{sensor}", f"led_{i}_ir", f"led_{i}_uv"], [sensor])
        for channel in ("ir", "uv"):
            edges([f"led_{i}_{channel}"], analog(f"current_led_{i}_{channel}"))
    for i in (1, 2):
        analog(f"current_mot_{i}")
        edges([f"pol_{i}"], analog(f"angle_{i}") + [f"angle_{i}_digital", "ir_3", "vis_3"])
    for i in (2, 3):
        edges([f"ir_{i-1}", f"slope_f{i}", f"intercept_f{i}"], [f"led_{i}_uv"])
    return graph


def graph_record(graph):
    is_dag = nx.is_directed_acyclic_graph(graph)
    strict_pairs = [[x, y] for x in sorted(graph) for y in sorted(nx.descendants(graph, x))
                    if not graph.has_edge(x, y)] if is_dag else None
    return {
        "nodes": sorted(graph), "edges": sorted(graph.edges),
        "node_count": len(graph), "edge_count": graph.number_of_edges(),
        "dag": is_dag, "strict_pairs_all_nodes": strict_pairs,
        "longest_directed_path_edges": nx.dag_longest_path_length(graph) if is_dag else None,
        "two_node_cycles": sorted(nx.simple_cycles(graph, length_bound=2)) if not is_dag else [],
        "cyclic_components": sorted(sorted(nodes) for nodes in nx.strongly_connected_components(graph)
                                    if len(nodes) > 1 or graph.has_edge(next(iter(nodes)), next(iter(nodes)))),
    }


def counts(series):
    return {str(key): int(count) for key, count in series.value_counts(dropna=False).items()}


def schema(frame):
    return {"rows": len(frame), "columns": len(frame.columns),
            "dtypes": {str(k): str(v) for k, v in frame.dtypes.items()},
            "missing": {k: int(v) for k, v in frame.isna().sum().items() if v}}


def protocol_rows(catalog, dataset):
    if dataset not in CONFIG_TABLES:
        return {}
    frame = pd.read_csv(catalog / "datasets" / dataset / CONFIG_TABLES[dataset])
    by_name = {}
    for item in frame.to_dict("records"):
        target = item.get("target", item.get("from"))
        endpoint = item.get("to")
        suffix = f"_{endpoint}" if pd.notna(endpoint) else ""
        by_name[f"validate_{target}{suffix}"] = (target, item)
    return by_name


def chamber_csv(frame, dataset, name, protocols, graph):
    result = schema(frame)
    if name in ("uniform_reference", "exp_1_low_noise", "exp_2_noisy"):
        result["constant_columns"] = sorted(frame.columns[frame.nunique(dropna=False) == 1])
    result["metadata_counts"] = {
        k: counts(frame[k]) for k in ("config", "intervention")
        if k in frame and frame[k].nunique() <= 30
    }
    if "flag" in frame:
        sizes = frame.groupby("flag", dropna=False).size()
        result["flag_groups"] = {"count": len(sizes), "rows_per_group": counts(sizes)}
    result["indices"] = {
        key: {"unique": int(frame[key].nunique()), "ordered": bool(frame[key].is_monotonic_increasing)}
        for key in ("counter", "timestamp") if key in frame
    }
    if "timestamp" in frame and pd.api.types.is_numeric_dtype(frame["timestamp"]) and len(frame) > 1:
        gaps = frame["timestamp"].diff().dropna()
        result["timestamp_gaps_native"] = [float(gaps.min()), float(gaps.median()), float(gaps.max())]
    if graph is not None:
        result["graph_missing_from_csv"] = sorted(set(graph) - set(frame))
        result["csv_outside_graph"] = sorted(set(frame) - set(graph) - set(META))
    targets = LEVELS.get(dataset, {})
    columns = targets.get(name, targets.get("*", []))
    if name in protocols:
        target, item = protocols[name]
        # Pressure feedback is an intervention on a sensor reading; use the assigned
        # arms and never summarize the measured pressure response as an action.
        result["assignment"] = {"target": target, "levels_flag_0_1": [item["xA"], item["xB"]],
                                "wait_ms": int(item["T"]), "planned_rows": int(item["N"]),
                                "flag_counts": counts(frame["flag"])}
        if target in frame and target != "pressure_downwind":
            # A hardware command column can be rounded without being an actual sensor readback.
            result["assignment"]["logged_command_by_flag"] = {
                str(flag): counts(group[target]) for flag, group in frame.groupby("flag")
            }
    result["command_rows"] = {key: counts(frame[key]) for key in columns if key in frame}
    if dataset == "wt_bernoulli_v1" and name.startswith("random_loads_"):
        blocks = frame.groupby("flag")["load_in"]
        result["load_in_assignment_blocks"] = counts(blocks.first())
        result["blocks_with_inconsistent_load_in"] = int((blocks.nunique() != 1).sum())
    if dataset == "lt_spice_v1" and len(frame) == 110_000:
        # The source generator documents 20 consecutive batches of 5,500.
        # Confirm timing but do not label them independent sessions.
        gaps = frame["timestamp"].diff()
        boundaries = list(range(5500, len(frame), 5500))
        result["documented_batch_boundary_gaps_seconds"] = [float(gaps.iloc[i]) for i in boundaries]
        result["green_command_batches_present"] = counts_by_level_across_batches(frame["green"])
        result["linked_path_columns_present"] = sorted(
            {"green", "ir_1", "led_2_uv", "current_led_2_uv", "current_led_2_uv_raw",
             "ir_2", "led_3_uv", "current_led_3_uv"} & set(frame)
        )
    return result


def counts_by_level_across_batches(commands):
    levels = {}
    for start in range(0, len(commands), 5500):
        for level in commands.iloc[start:start + 5500].dropna().unique():
            key = str(level)
            levels[key] = levels.get(key, 0) + 1
    return levels


def inspect_comparison(path, kind):
    if kind == "ess_archive":
        with zipfile.ZipFile(path) as archive:
            members = [i for i in archive.namelist() if i.startswith("accp_dataset_reduced/Period_")
                       and i.lower().endswith(".csv")]
            periods = {}
            for member in members:
                periods.setdefault(member.split("/")[1], []).append(member)
            samples = {}
            for period, names in sorted(periods.items()):
                member = sorted(names)[0]
                with archive.open(member) as stream:
                    frame = pd.read_csv(stream, encoding="latin1", sep=None, engine="python")
                samples[period] = {"member": member, "csv_members": len(names), **schema(frame)}
            return samples
    if kind == "ess_graph":
        matrix = pd.read_csv(path, index_col=0)
        graph = nx.DiGraph()
        graph.add_nodes_from(matrix.index)
        graph.add_edges_from((col, row) for row in matrix.index for col in matrix.columns
                             if row != col and matrix.loc[row, col] != 0)
        return graph_record(graph)
    if kind == "comparison_csv":
        return schema(pd.read_csv(path, low_memory=False))
    if kind == "assembly_graph":
        graph = nx.adjacency_graph(json.loads(path.read_text(encoding="utf-8")))
        return graph_record(graph)
    if kind == "causalman_graph":
        graph = nx.read_graphml(path)
        # Serialized GraphML is directed, but edge semantics must also be checked.
        return {
            "serialized_graph": graph_record(graph),
            "edge_attribute_names": sorted({key for _, _, attrs in graph.edges(data=True) for key in attrs}),
            "edge_types": counts(pd.Series([attrs.get("edge_type", "untyped")
                                            for _, _, attrs in graph.edges(data=True)])),
        }
    return None


def inspect(manifest, folder, catalog, download=False):
    catalog_head = subprocess.check_output(["git", "-C", str(catalog), "rev-parse", "HEAD"],
                                           text=True).strip()
    if catalog_head != manifest["catalog_commit"]:
        raise ValueError("Dataset catalog checkout must match the manifest commit")
    protocol_paths = [f"datasets/{dataset}/{name}" for dataset, name in CONFIG_TABLES.items()]
    subprocess.run(["git", "-C", str(catalog), "diff", "--quiet", "HEAD", "--", *protocol_paths],
                   check=True)
    artifacts = {}
    report = {"pandas": pd.__version__, "networkx": nx.__version__, "artifacts": artifacts}
    wheel, artifacts["mk1_wheel"] = retrieve(manifest["mk1_wheel"], folder, download)
    graphs = load_mk1_graphs(wheel)
    report["mk1_graphs"] = {key: graph_record(graph) for key, graph in graphs.items()}
    graphs["mk2_linked_leds"] = linked_leds_figure()
    report["mk2_figure_transcription"] = graph_record(graphs["mk2_linked_leds"])
    datasets = {}
    comparison = {}
    for dataset, entry in manifest["datasets"].items():
        path, artifacts[dataset] = retrieve(entry, folder, download)
        if entry["kind"] != "chamber":
            result = inspect_comparison(path, entry["kind"])
            if result is not None:
                comparison[dataset] = result
            continue
        protocols = protocol_rows(catalog, dataset)
        graph = graphs.get(entry.get("graph"))
        experiments = {}
        with zipfile.ZipFile(path) as archive:
            for member in sorted(archive.namelist()):
                if not member.endswith(".csv"):
                    continue
                with archive.open(member) as stream:
                    frame = pd.read_csv(stream, low_memory=False)
                name = Path(member).stem
                experiments[name] = chamber_csv(frame, dataset, name, protocols, graph)
        datasets[dataset] = {"experiment_csv_count": len(experiments), "experiments": experiments}
    report["chamber"] = datasets
    report["comparison"] = comparison
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "dataset_manifest.json").read_text(encoding="utf-8"))
    args.data.mkdir(parents=True, exist_ok=True)
    report = inspect(manifest, args.data, args.catalog, args.download)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
