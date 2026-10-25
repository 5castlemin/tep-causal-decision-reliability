# Actual execution (local absolute paths replaced by roles)

```text
<existing-isolated-python> -X utf8 -m unittest discover -s tests -p test_diverse_structure_pilot.py -v
<existing-isolated-python> -X utf8 scripts/run_diverse_structure_pilot.py --module <pinned models_fcm.py> --output research_runs/diverse_structure_pilot/run_v1 --raw-log-dir <task archive>/학습_원시console
<existing-isolated-python> -X utf8 scripts/export_diverse_reference_graphs.py
<existing-isolated-python> -X utf8 scripts/render_diverse_overview.py
<existing-isolated-python> -X utf8 -m unittest discover -s tests -p test_diverse_metric_analysis.py -v
<existing-isolated-python> -X utf8 scripts/analyze_diverse_structure_pilot.py
<existing-isolated-python> -X utf8 scripts/validate_diverse_structure_pilot.py
```

All above returned0. Every learner is a real child process using the same isolated interpreter:

```text
<existing-isolated-python> -X utf8 scripts/learn_diverse_graph.py --train <dataset>/train.csv --config <dataset>/<algorithm>_learner_config.json --output <dataset>/<algorithm>_graph.json
```

144 child learning attempts completed, no timeouts/nonzero exits. Individual input hashes/configurations and sanitized stdout/stderr are beside the graphs; original console hashes are in RAW_CONSOLE_PROVENANCE.json. The staged acceptance has2structures first, then6more; all pass before the first learner starts. All918 discovery-policy decisions and120 controlled decisions are frozen before any final holdout. Source/API repeated calls are not independent datasets. Reported run wall duration is1001.555323seconds including worker imports/evaluation; native learner durations are separately saved.
