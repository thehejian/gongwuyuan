#!/usr/bin/env python3
"""省考行测隐蔽刷题 CLI：draw 出题 / check 判分 / stats 正确率 / wrong 错题重做"""
import json, os, random, re, sys, time, glob

ROOT = os.path.expanduser("~/gongwuyuan")
BANK = os.path.join(ROOT, "省考真题/行测真题库-xingcezhenti")
INDEX = os.path.join(ROOT, "题库索引.json")
STATE = os.path.join(ROOT, "刷题状态.json")

TAG = re.compile(r"<[^>]+>")
ANS = re.compile(r"\*\*答案\*\*[:：]\s*([A-D])")
QID = re.compile(r"qid\s+(\d+)")
MODS = ["01-政治理论", "02-常识判断", "03-言语理解与表达",
        "04-数量关系", "05-判断推理", "06-资料分析"]
WEIGHT = {"01-政治理论": 8, "02-常识判断": 12, "03-言语理解与表达": 25,
          "04-数量关系": 10, "05-判断推理": 30, "06-资料分析": 15}

def clean(html):
    html = re.sub(r'<img[^>]*>', '', html)
    html = re.sub(r'</p>\s*<p>', '\n', html)
    html = TAG.sub('', html)
    html = html.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    return re.sub(r'[ \t\u3000]+', ' ', html).strip()

def build_index():
    items = []
    for mod in MODS:
        for f in sorted(glob.glob(os.path.join(BANK, mod, "*.md"))):
            base = os.path.basename(f)
            if "2026年" in base:      # 2026 卷留给模考
                continue
            txt = open(f, encoding="utf-8").read()
            parts = re.split(r"^## 第 (\d+) 题", txt, flags=re.M)
            for i in range(1, len(parts) - 1, 2):
                no, body = parts[i], parts[i + 1]
                am = ANS.search(body)
                if not am:
                    continue
                stem_h = body.split("- **A**")[0]
                stem = clean(stem_h.split("\n\n", 1)[-1] if stem_h.startswith("##") else stem_h)
                # 去掉题号头（<sub>…</sub> 已在 clean 中变纯文本，删掉 qid 行残留）
                stem = re.sub(r"^第 \d+ 题.*?\n", "", stem, flags=re.S)
                opts = dict(re.findall(r"^- \*\*([A-D])\*\*\.?\s*(.*?)\s*$",
                                       body, flags=re.M))
                opts = {k: v.replace("✅", "").replace("　", " ").strip()
                        for k, v in opts.items()}
                if not stem or len(stem) < 12 or set(opts.values()) <= {"A", "B", "C", "D"}:
                    continue
                if len(opts) != 4:
                    continue
                qm = QID.search(body[:400])
                exp_h = body.split("**官方解析**", 1)[1] if "**官方解析**" in body else ""
                exp = clean(exp_h)
                items.append({
                    "id": "%s#%s" % (base[:20], no),
                    "qid": qm.group(1) if qm else "",
                    "mod": mod.split("-", 1)[1],
                    "file": os.path.relpath(f, BANK),
                    "no": int(no),
                    "stem": stem, "opts": opts,
                    "ans": am.group(1), "exp": exp[:400],
                })
    json.dump(items, open(INDEX, "w", encoding="utf-8"), ensure_ascii=False)
    return items

def load():
    if not os.path.exists(INDEX):
        build_index()
    idx = json.load(open(INDEX, encoding="utf-8"))
    st = {"done": {}, "wrong": [], "pending": None,
          "stats": {}}
    if os.path.exists(STATE):
        st.update(json.load(open(STATE, encoding="utf-8")))
    return idx, st

def save(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def draw(mod=None, n_wrong=False, include2026=False):
    idx, st = load()
    done = set(st["done"])
    pool = [q for q in idx if q["id"] not in done]
    if n_wrong:
        w = set(st["wrong"])
        pool = [q for q in pool if q["id"] in w] or \
               [q for q in idx if q["id"] in set(st["wrong"])]
    if mod:
        pool = [q for q in pool if q["mod"] == mod]
    if not pool:
        print("EMPTY 该范围内题目已做完"); return
    # 加权抽模块
    if not mod and not n_wrong:
        wts = [WEIGHT.get(q["mod"], 10) for q in pool]
        q = random.choices(pool, weights=wts)[0]
    else:
        q = random.choice(pool)
    st["pending"] = q
    save(st)
    print("第1题 · %s · [%s]" % (q["mod"], q.get("qid") or q["id"]))
    print(q["stem"])
    print()
    for k in "ABCD":
        print("%s. %s" % (k, q["opts"][k]))
    print("\n（回复 A/B/C/D，或 skip 跳过）")

def check(ans):
    idx, st = load()
    q = st.get("pending")
    if not q:
        print("无待判题目，先 draw"); return
    ans = ans.strip().upper()[:1]
    if ans == "S":   # skip
        st["done"][q["id"]] = "skip"
        st["pending"] = None
        save(st); print("已跳过"); return
    ok = ans == q["ans"]
    st["done"][q["id"]] = ans
    if ok:
        print("✓ 对")
    else:
        print("✗ 错，你答%s，正确%s" % (ans or "空", q["ans"]))
        if q["id"] not in st["wrong"]:
            st["wrong"].append(q["id"])
    s = st["stats"].setdefault(q["mod"], [0, 0])
    s[0] += 1; s[1] += 1 if ok else 0
    print("解析:", (q["exp"] or "（无）")[:300])
    st["pending"] = None
    save(st)

def stats():
    idx, st = load()
    print("已做 %d 题，错题 %d" % (len(st["done"]), len(st["wrong"])))
    for m, (n, r) in sorted(st["stats"].items()):
        print("  %s: %d/%d = %d%%" % (m, r, n, round(100 * r / n)))

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "draw"
    if c == "build":
        print("index:", len(build_index()))
    elif c == "draw":
        draw(sys.argv[2] if len(sys.argv) > 2 else None)
    elif c == "wrong":
        draw(n_wrong=True)
    elif c == "check":
        check(sys.argv[2])
    elif c == "stats":
        stats()
