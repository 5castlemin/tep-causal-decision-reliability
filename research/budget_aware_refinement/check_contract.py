"""Check document contract declarations, not experiment results."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
FILES=("README.md","RESEARCH_PROTOCOL.md","ROADMAP.md","RESEARCH_STATUS.md","DECISION_LOG.md","EXPERIMENT_REGISTRY.md","RISKS_AND_LIMITATIONS.md","MERGE_CHECKLIST.md","LITERATURE_NOVELTY_MATRIX.md","ARCHIVED_METRIC_COMBINATION_DESIGN.md")
def main():
 d={name:(ROOT/name).read_text(encoding="utf8") for name in FILES}
 assert all(d.values())
 assert all(x in d["RESEARCH_PROTOCOL.md"] for x in ("FN","FP","REV","14개","gamma=1","ddof=1","Holm","Step4"))
 assert all(re.search(r"Step ?"+str(i)+r"\b",d["ROADMAP.md"]) for i in range(10))
 assert "Step0 DONE" in d["RESEARCH_STATUS.md"] and "Step1 NOT_STARTED" in d["RESEARCH_STATUS.md"]
 assert "[x] ~~Step 0" in d["ROADMAP.md"] and "Step 8" in d["ROADMAP.md"] and "BLOCKED" in d["ROADMAP.md"]
 assert "archived design" in d["ARCHIVED_METRIC_COMBINATION_DESIGN.md"]
 assert all(x in d["LITERATURE_NOVELTY_MATRIX.md"] for x in ("ABCD", "Causal Bandits", "Predict, then Optimize"))
 print("PASS: Step0 declaration and document consistency; no scientific result validated")
if __name__=="__main__":main()
