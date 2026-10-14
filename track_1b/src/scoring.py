"""Pilot scoring 0.5. Python 3.10+, standard library only.

The LLM assesses content. This module computes points and output labels.
It never infers legal correctness from lexical overlap.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
VERSION = "0.5"
CREDIT = {"met": Fraction(1), "partial": Fraction(1, 2), "missing": Fraction(0), "contradicted": Fraction(0)}
STATUSES = set(CREDIT) | {"uncertain"}
DECISIONS = {"met", "missing", "contradicted", "uncertain"}
LABELS = {"correct", "incorrect", "not_attempted"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalise(text):
    return re.sub(r"\s+", " ", text).strip()


def quote_is_present(quote, text):
    return isinstance(quote, str) and bool(normalise(quote)) and normalise(quote) in normalise(text)


def load_items(path):
    data = read_json(path)
    if data.get("metadata", {}).get("grading_rules_version") != VERSION:
        raise ValueError("Der Fragenkatalog muss ausdrücklich Version 0.5 ausweisen.")
    items = {}
    for item in data["items"]:
        if item["id"] in items:
            raise ValueError("Doppelte Frage-ID.")
        groups = [f["fact_id"] for f in item["facts"]]
        criteria = [c["criterion_id"] for c in item["criteria"]]
        if not groups or len(groups) != len(set(groups)) or not criteria or len(criteria) != len(set(criteria)):
            raise ValueError("Ungültige oder doppelte Kriterien-IDs.")
        if set(c["fact_id"] for c in item["criteria"]) != set(groups):
            raise ValueError("Jedes Pflichtkriterium braucht mindestens einen zugeordneten Inhalt.")
        policy = item["scoring_policy"]
        share = policy.get("critical_weight_share")
        if isinstance(share, bool) or not isinstance(share, (int, float)) or not 0 < share < 1:
            raise ValueError("Ungültiger Gewichtsanteil wesentlicher Inhalte.")
        threshold = policy["threshold_percent"]
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
            raise ValueError("Ungültige Prozentgrenze.")
        for cid, minimum in policy["critical_criteria"].items():
            if cid not in criteria or isinstance(minimum, bool) or minimum not in (0.5, 1):
                raise ValueError("Ungültige wesentliche Inhalte.")
        target_count = policy.get("list_target_count")
        if target_count is not None and (type(target_count) is not int or not 1 <= target_count <= len(groups) or policy["critical_criteria"]):
            raise ValueError("Ungültige offene Mindestliste.")
        minimum_groups = policy["minimum_fully_met_groups"]
        if type(minimum_groups) is not int or not 0 <= minimum_groups <= len(groups):
            raise ValueError("Ungültige Mindestzahl vollständig erfüllter Aufgaben.")
        source_ids = [s["source_id"] for s in item["source_excerpts"]]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Doppelte Quellen-ID.")
        items[item["id"]] = item
    return data["metadata"], items


def load_responses(path, items):
    responses = read_json(path)
    if not isinstance(responses, list) or not responses:
        raise ValueError("Antwortdatei muss eine nicht leere JSON-Liste sein.")
    seen = set()
    for r in responses:
        for key in ("response_id", "item_id", "model_id"):
            if not isinstance(r.get(key), str) or not r[key].strip():
                raise ValueError(f"{key} fehlt.")
        if r["response_id"] in seen or r["item_id"] not in items:
            raise ValueError("Doppelte Antwort oder unbekannte Frage.")
        if not isinstance(r.get("model_response"), str):
            raise ValueError("Ein technischer Fehler oder null ist keine Modellantwort.")
        seen.add(r["response_id"])
    return responses


def validate_judgment(j, response, item):
    rid = response["response_id"]
    if j.get("response_id") != rid or j.get("item_id") != item["id"]:
        raise ValueError(f"{rid}: IDs stimmen nicht überein.")
    for field in ("not_attempted", "needs_review"):
        if type(j.get(field)) is not bool:
            raise ValueError(f"{rid}: {field} muss boolesch sein.")
    if type(j.get("rubric_conflict", False)) is not bool:
        raise ValueError(f"{rid}: rubric_conflict muss boolesch sein.")
    if j.get("rubric_conflict", False) and not j["needs_review"]:
        raise ValueError(f"{rid}: Ein Rasterkonflikt braucht Durchsicht.")
    if not isinstance(j.get("reason"), str) or not j["reason"].strip():
        raise ValueError(f"{rid}: Begründung fehlt.")
    criteria = j.get("criteria")
    if not isinstance(criteria, list) or not all(isinstance(c, dict) for c in criteria):
        raise ValueError(f"{rid}: Einzelbewertungen fehlen.")
    ids = [c.get("criterion_id") for c in criteria]
    if len(ids) != len(set(ids)) or set(ids) != {c["criterion_id"] for c in item["criteria"]}:
        raise ValueError(f"{rid}: Fehlende, zusätzliche oder doppelte Inhalte.")
    for c in criteria:
        if c.get("status") not in STATUSES or not isinstance(c.get("reason"), str) or not c["reason"].strip():
            raise ValueError(f"{rid}: Ungültiger Status oder fehlende Begründung.")
        quote = c.get("response_quote")
        if not isinstance(quote, str):
            raise ValueError(f"{rid}: response_quote muss eine Zeichenkette sein.")
        if c["status"] in {"met", "partial", "contradicted"} and not quote_is_present(quote, response["model_response"]):
            raise ValueError(f"{rid}: Belegzitat fehlt oder kommt in der Antwort nicht vor.")
        if quote and not quote_is_present(quote, response["model_response"]):
            raise ValueError(f"{rid}: Belegzitat ist nicht im Antworttext enthalten.")
    decision = j.get("decision_status")
    if item["expected_decision"] is None:
        if decision != "not_applicable":
            raise ValueError(f"{rid}: Ohne erwartete Entscheidung ist not_applicable erforderlich.")
    elif decision not in DECISIONS:
        raise ValueError(f"{rid}: Ungültiger Entscheidungsstatus.")
    extra = j.get("extra_errors")
    unresolved = j.get("unverified_claims")
    if not isinstance(extra, list) or not isinstance(unresolved, list):
        raise ValueError(f"{rid}: Zusatzfehler und ungeklärte Aussagen müssen Listen sein.")
    sources = {s["source_id"]: s["text"] for s in item["source_excerpts"]}
    for e in extra:
        if not isinstance(e, dict) or e.get("severity") not in {"minor", "material"}:
            raise ValueError(f"{rid}: Ungültiger Zusatzfehler.")
        if not quote_is_present(e.get("response_quote"), response["model_response"]):
            raise ValueError(f"{rid}: Zusatzfehler muss die tatsächliche Aussage belegen.")
        if e.get("source_id") not in sources or not quote_is_present(e.get("basis_quote"), sources[e["source_id"]]):
            raise ValueError(f"{rid}: Zusatzfehler braucht ein belegbares Quellenzitat.")
        if not isinstance(e.get("reason"), str) or not e["reason"].strip():
            raise ValueError(f"{rid}: Bedeutung des Zusatzfehlers fehlt.")
    for e in unresolved:
        if not isinstance(e, dict) or e.get("label_impact") not in {"minor", "material", "uncertain"}:
            raise ValueError(f"{rid}: Ungeklärte Aussage braucht label_impact.")
        if not isinstance(e, dict) or not quote_is_present(e.get("response_quote"), response["model_response"]):
            raise ValueError(f"{rid}: Ungeklärte Aussage braucht ein Antwortzitat.")
        if not isinstance(e.get("reason"), str) or not e["reason"].strip():
            raise ValueError(f"{rid}: Offener Prüfpunkt fehlt.")
    uncertainty = decision == "uncertain" or any(c["status"] == "uncertain" for c in criteria) or any(e["label_impact"] != "minor" for e in unresolved)
    if uncertainty and not j["needs_review"]:
        raise ValueError(f"{rid}: Unsicherheit muss zur Durchsicht markiert werden.")
    if j["not_attempted"]:
        if any(c["status"] != "missing" for c in criteria) or extra or unresolved:
            raise ValueError(f"{rid}: Nichtbeantwortung widerspricht Inhaltsbewertungen.")
        if item["expected_decision"] is not None and decision != "missing":
            raise ValueError(f"{rid}: Bei Nichtbeantwortung fehlt die Entscheidung.")
    if not response["model_response"].strip() and not j["not_attempted"]:
        raise ValueError(f"{rid}: Leere Antwort ist not_attempted.")
    for prohibited in ("label", "score_percent", "points_earned", "has_material_extra_error"):
        if prohibited in j:
            raise ValueError(f"{rid}: {prohibited} wird vom Code berechnet und gehört nicht in die Judge-Ausgabe.")


def criterion_weights(item):
    groups = item["facts"]
    denominator = item["scoring_policy"].get("list_target_count", len(groups))
    weights = {c["criterion_id"]: Fraction(1, denominator * sum(d["fact_id"] == c["fact_id"] for d in item["criteria"])) for c in item["criteria"]}
    critical = set(item["scoring_policy"]["critical_criteria"])
    if critical and critical != set(weights):
        share = Fraction(str(item["scoring_policy"]["critical_weight_share"]))
        core_total = sum(weights[c] for c in critical)
        other_total = 1 - core_total
        weights = {c: w * (share / core_total if c in critical else (1-share) / other_total) for c,w in weights.items()}
    return weights


def score_judgment(j, response, item):
    validate_judgment(j, response, item)
    by_id = {c["criterion_id"]: c for c in j["criteria"]}
    groups = []
    lower_total = Fraction(0)
    upper_total = Fraction(0)
    for fact in item["facts"]:
        children = [c for c in item["criteria"] if c["fact_id"] == fact["fact_id"]]
        statuses = [by_id[c["criterion_id"]]["status"] for c in children]
        lower = sum((CREDIT.get(s, Fraction(0)) for s in statuses), Fraction(0)) / len(children)
        upper = sum((CREDIT.get(s, Fraction(1)) for s in statuses), Fraction(0)) / len(children)
        lower_total += lower
        upper_total += upper
        groups.append({"fact_id": fact["fact_id"], "credit": float(lower) if lower == upper else None,
                       "credit_range": [float(lower), float(upper)], "fully_met": all(s == "met" for s in statuses)})
    n = len(groups)
    coverage_percent = lower_total * 100 / n if lower_total == upper_total else None
    weights = criterion_weights(item)
    lower_percent = sum((weights[cid] * CREDIT.get(c["status"], Fraction(0)) for cid,c in by_id.items()), Fraction(0)) * 100
    upper_percent = sum((weights[cid] * CREDIT.get(c["status"], Fraction(1)) for cid,c in by_id.items()), Fraction(0)) * 100
    lower_percent = min(Fraction(100), lower_percent)
    upper_percent = min(Fraction(100), upper_percent)
    policy = item["scoring_policy"]
    blockers = []
    if not j["not_attempted"]:
        if item["expected_decision"] is not None and j["decision_status"] not in {"met", "uncertain"}:
            blockers.append("Gefragte Fallentscheidung fehlt oder ist falsch.")
        if any(c["status"] == "contradicted" for c in j["criteria"]):
            blockers.append("Ein gefragter Inhalt wird ausdrücklich falsch dargestellt.")
        if any(e["severity"] == "material" for e in j["extra_errors"]):
            blockers.append("Belegter wesentlicher Zusatzfehler.")
        for cid, minimum in policy["critical_criteria"].items():
            status = by_id[cid]["status"]
            if status != "uncertain" and CREDIT[status] < Fraction(str(minimum)):
                blockers.append(f"Wesentlicher Inhalt {cid} nicht ausreichend erfüllt.")
        possible_groups = sum(all(by_id[c["criterion_id"]]["status"] in {"met","uncertain"} for c in item["criteria"] if c["fact_id"] == fact["fact_id"]) for fact in item["facts"])
        if possible_groups < policy["minimum_fully_met_groups"]:
            blockers.append("Explizite Mindestzahl vollständig genannter Aufgaben nicht erreicht.")
        if upper_percent < Fraction(str(policy["threshold_percent"])):
            blockers.append("Inhaltsscore unter der vorläufigen Prozentgrenze.")
    if j.get("rubric_conflict", False):
        label = None
    elif blockers:
        label = "incorrect"
    elif j["needs_review"]:
        label = None
    elif j["not_attempted"]:
        label = "not_attempted"
    else:
        label = "incorrect" if blockers else "correct"
    return {
        "response_id": response["response_id"], "item_id": item["id"], "model_id": response["model_id"],
        "judge_label": label, "needs_review": j["needs_review"],
        "points_earned": float(lower_percent) if lower_percent == upper_percent else None, "points_possible": 100,
        "score_percent": round(float(lower_percent), 2) if lower_percent == upper_percent else None,
        "coverage_percent_v03": round(float(coverage_percent),2) if coverage_percent is not None else None,
        "criterion_weights": {cid: float(w) for cid,w in weights.items()},
        "rubric_conflict": j.get("rubric_conflict",False),
        "review_affects_label": j["needs_review"] and label is None,
        "score_range_percent": [round(float(lower_percent), 2), round(float(upper_percent), 2)],
        "fully_met_groups": sum(g["fully_met"] for g in groups), "fact_scores": groups,
        "criteria": j["criteria"], "decision_status": j["decision_status"],
        "has_material_extra_error": any(e["severity"] == "material" for e in j["extra_errors"]),
        "extra_errors": j["extra_errors"], "unverified_claims": j["unverified_claims"],
        "label_blockers": blockers, "reason": j["reason"], "human_label": None,
    }


def evaluate(responses, items, judge_files, gold_path=None, adjudications_path=None):
    by_response = {r["response_id"]: r for r in responses}
    judgments = {}
    for path in judge_files:
        data = read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("judgments"), list):
            raise ValueError(f"{path}: judgments fehlt.")
        for j in data["judgments"]:
            rid = j.get("response_id")
            if rid not in by_response or rid in judgments:
                raise ValueError("Unbekannte oder doppelte Antwort-ID.")
            r = by_response[rid]
            judgments[rid] = score_judgment(j, r, items[r["item_id"]])
    gold = {}
    if gold_path:
        gold_rows = read_json(gold_path)
        gold = {r["response_id"]: r for r in gold_rows}
        if len(gold) != len(gold_rows) or set(gold) != set(by_response):
            raise ValueError("Sollurteile passen nicht genau zu dieser Antwortsammlung.")
        for g in gold_rows:
            if g.get("proposed_label") not in LABELS | {None} or g.get("human_label") not in LABELS | {None}:
                raise ValueError("Ungültiges Sollurteil.")
    rows = []
    adjudications = {}
    if adjudications_path:
        entries = read_json(adjudications_path)
        for a in entries:
            rid = a.get("response_id")
            if rid not in by_response or rid in adjudications or a.get("label") not in LABELS:
                raise ValueError("Ungültige oder doppelte gemeinsame Durchsicht.")
            if not a.get("reason") or not a.get("source"):
                raise ValueError("Durchsicht braucht Begründung und Herkunft.")
            adjudications[rid] = a
    for r in responses:
        rid = r["response_id"]
        row = judgments.get(rid, {"response_id": rid, "item_id": r["item_id"], "model_id": r["model_id"],
                                 "judge_label": None, "needs_review": False, "score_percent": None,
                                 "score_range_percent": None, "reason": "Noch keine Einzelbewertungen vorhanden.", "human_label": None})
        row = {**r, **row, "missing_judgment": rid not in judgments, "proposed_label": gold.get(rid, {}).get("proposed_label"),
               "human_label": gold.get(rid, {}).get("human_label")}
        a = adjudications.get(rid)
        row["final_label"] = a["label"] if a else row["judge_label"]
        row["label_source"] = a["source"] if a else "scoring_rules"
        row["adjudication"] = a
        if a:
            row["review_affects_label"] = False
        rows.append(row)
    metrics = {}
    for model in sorted({r["model_id"] for r in rows}):
        group = [r for r in rows if r["model_id"] == model]
        counts = Counter(r["final_label"] for r in group if r["final_label"] is not None)
        finalized = sum(counts.values())
        score_rows = [r for r in group if r["score_percent"] is not None]
        complete = finalized == len(group)
        metrics[model] = {"total_responses": len(group), "finalized": finalized,
                          "correct": counts["correct"], "incorrect": counts["incorrect"], "not_attempted": counts["not_attempted"],
                          "pending_review": sum(r["needs_review"] and r["final_label"] is None for r in group),
                          "additional_review": sum(r["needs_review"] and r["final_label"] is not None for r in group),
                          "missing_judgments": sum(r["missing_judgment"] for r in group),
                          "accuracy": counts["correct"] / len(group) if complete else None,
                          "abstention_rate": counts["not_attempted"] / len(group) if complete else None,
                          "score_observations": len(score_rows),
                          "mean_observed_content_score": sum(r["score_percent"] for r in score_rows) / len(score_rows) if score_rows else None}
    agreement = {}
    for field in ("proposed_label", "human_label"):
        compared = [r for r in rows if r["judge_label"] is not None and r[field] is not None]
        agreement[field] = {"n": len(compared), "agreement": sum(r["judge_label"] == r[field] for r in compared) / len(compared) if compared else None}
    return {"grading_rules_version": VERSION, "threshold_status": "provisional_not_calibrated",
            "metrics_by_model": metrics, "agreement": agreement, "rows": rows,
            "judge_files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in judge_files}}


def report_text(result):
    lines = ["# Auswertung mit Teilpunkten", "", "Bewertungsregeln 0.5. Gewichtung und Prozentgrenze vorläufig. Inhaltsscore ist keine Wahrscheinlichkeit der Richtigkeit.", ""]
    for model, m in result["metrics_by_model"].items():
        lines += [f"Modell: {model}", "", f"{m['correct']} korrekt, {m['incorrect']} nicht korrekt und {m['not_attempted']} nicht beantwortet.",
                  f"{m['pending_review']} zur Durchsicht. {m['missing_judgments']} Bewertungen fehlen.",
                  f"Gesamtquote: {m['accuracy']:.1%}." if m["accuracy"] is not None else "Gesamtquote bleibt offen.", ""]
    lines += ["| Frage | Inhaltsscore | Label | Grund |", "|---|---:|---|---|"]
    for r in result["rows"]:
        score = f"{r['score_percent']:.1f} %" if r["score_percent"] is not None else "offen"
        label = r["final_label"] or ("Durchsicht" if r["needs_review"] else "ausstehend")
        reason = r["reason"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {r['item_id']} | {score} | {label} | {reason} |")
    lines += ["", "Der Inhaltsscore zeigt richtige Bestandteile auch bei einem wesentlichen Fehler. Hohe Teilpunkte garantieren deshalb kein correct.",
              "Vorgeschlagene Sollurteile und redaktionelle Vorbewertungen sind keine menschlich bestätigten Bewertungen.", ""]
    return "\n".join(lines)


def make_packets(responses, items, output, batch_size=8):
    if batch_size < 1:
        raise ValueError("Paketgrösse muss positiv sein.")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    prompt = (ROOT / "judge_prompt.txt").read_text(encoding="utf-8")
    files = []
    for start in range(0, len(responses), batch_size):
        tasks = []
        for r in responses[start:start + batch_size]:
            item = items[r["item_id"]]
            tasks.append({"response_id": r["response_id"], "item_id": item["id"], "question": item["question"],
                          "reference_answer": item["reference_answer"], "expected_decision": item["expected_decision"],
                          "required_facts": item["facts"], "criteria": item["criteria"], "grading_note": item["grading_note"],
                          "source_excerpts": item["source_excerpts"], "model_response": r["model_response"]})
        path = output / f"{start // batch_size + 1:02d}_pruefpaket.txt"
        path.write_text(prompt + "\n\nZU PRÜFENDE DATEN\n" + json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append(path)
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bewertungsprototyp mit Teilpunkten, Version 0.5")
    parser.add_argument("command", choices=["packets", "score"])
    parser.add_argument("--items", type=Path, default=ROOT / "data/items.json")
    parser.add_argument("--responses", type=Path, default=ROOT / "data/pilot_antworten.json")
    parser.add_argument("--judge-dir", type=Path, default=ROOT / "judge_antworten")
    parser.add_argument("--out", type=Path, default=ROOT / "ergebnisse")
    parser.add_argument("--gold", type=Path)
    parser.add_argument("--adjudications", type=Path)
    args = parser.parse_args(argv)
    _, items = load_items(args.items)
    responses = load_responses(args.responses, items)
    if args.command == "packets":
        for path in make_packets(responses, items, args.out):
            print(path)
    else:
        files = sorted(args.judge_dir.glob("*.json"))
        result = evaluate(responses, items, files, args.gold, args.adjudications)
        write_json(args.out / "ergebnis.json", result)
        text = report_text(result)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "auswertung.md").write_text(text, encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
