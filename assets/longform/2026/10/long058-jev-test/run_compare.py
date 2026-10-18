#!/usr/bin/env python3
"""Run every item in questions.json on Jev (TypeSafe /v1/systemone) and GPT-6 Luna (OpenAI /v1/decisions).
One question per request, same image file, same question text. Raw responses go to runs/<model>/<id>.json.
Keys: TYPESAFE_API_KEY and OPENAI_API_KEY from the environment. Nothing is printed but ids, answers and timings.
  python3 run_compare.py --items questions.json [--models jev-1.14.0,gpt-6-luna]"""
import argparse, base64, json, os, time, urllib.request, urllib.error
from pathlib import Path
R = Path(__file__).resolve().parent
OAI = os.environ["OPENAI_API_KEY"]

def post(url, body, headers, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**headers, "Content-Type": "application/json"})
    t = time.perf_counter()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=timeout)); return r, time.perf_counter() - t, None
    except urllib.error.HTTPError as e:
        return None, time.perf_counter() - t, f"HTTP {e.code} {e.read()[:300]!r}"
    except Exception as e:
        return None, time.perf_counter() - t, repr(e)[:300]

def jev(it, model):
    state, assets = {}, {}
    if it["image"]:
        b = base64.b64encode((R / it["image"]).read_bytes()).decode()
        state["image"] = "img-1"; assets["img-1"] = {"type": "image", "format": "jpg", "data_base64": b}
    if it["state_text"]:
        state["text"] = it["state_text"]
    ref = "`image`" if it["image"] else "`text`"
    q = {"type": it["qtype"], "instructions": f"{it['question']} ({ref} 기준)"}
    if it["qtype"] == "choice":
        q["criteria"] = it["choices"]
    body = {"model": model, "state": state, "questions": {"q": q}}
    if assets: body["assets"] = assets
    h = {"Authorization": "Bearer " + os.environ["TYPESAFE_API_KEY"]}
    if it["image"]: h["TypeSafe-Danger-Zone-Images"] = "true"
    r, dt, err = post("https://api.typesafe.ai/v1/systemone", body, h)
    if err: return {"error": err, "latency": dt}
    a = r["answers"]["q"]
    ans = a.get("noul") if it["qtype"] == "noul" else a.get("choice")
    return {"answer": ans, "confidence": a.get("confidence"), "latency": dt, "tokens": r.get("usage", {}).get("input_tokens"), "raw": r}

def luna(it, model):
    content = []
    if it["state_text"]:
        content.append({"type": "input_text", "text": it["state_text"]})
    if it["image"]:
        b = base64.b64encode((R / it["image"]).read_bytes()).decode()
        content.append({"type": "input_text", "text": "image:"}); content.append({"type": "input_image", "image_url": "data:image/jpeg;base64," + b})
    q = {"name": "q", "instructions": it["question"]}
    if it["qtype"] == "noul":
        q["type"] = "predicate"
    else:
        q["type"] = "choice"; q["choices"] = [{"value": k, "description": v} for k, v in it["choices"].items()]
    body = {"model": model, "input": [{"role": "user", "content": content}], "questions": [q]}
    r, dt, err = post("https://api.openai.com/v1/decisions", body, {"Authorization": "Bearer " + OAI})
    if err: return {"error": err, "latency": dt}
    a = r["answers"][0]
    ans = a.get("probability") if it["qtype"] == "noul" else a.get("choice")
    return {"answer": ans, "confidence": a.get("confidence"), "latency": dt, "tokens": r.get("usage", {}).get("input_tokens"), "raw": r}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--models", default="jev-1.14.0,gpt-6-luna"); ap.add_argument("--only"); ap.add_argument("--items", default="items.json")
    a = ap.parse_args()
    items = json.loads((R / (a.items if hasattr(a, "items") else "items.json")).read_text())
    for model in a.models.split(","):
        out = R / "runs" / model; out.mkdir(parents=True, exist_ok=True)
        for it in items:
            if a.only and a.only not in it["id"]: continue
            res = (luna if model.startswith("gpt") else jev)(it, model)
            res.update({"id": it["id"], "model": model, "truth": it["truth"], "qtype": it["qtype"]})
            if "answer" in res:
                pred = (res["answer"] > 0.5) if it["qtype"] == "noul" else res["answer"]
                res["correct"] = pred == it["truth"]
            (out / f"{it['id']}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
            print(model, it["id"], res.get("answer"), "OK" if res.get("correct") else ("ERR " + res["error"][:120] if "error" in res else "WRONG"), f"{res['latency']:.2f}s", flush=True)
main()
