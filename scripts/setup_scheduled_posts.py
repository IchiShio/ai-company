#!/usr/bin/env python3
"""batch-001 Day1-3の6投稿をlaunchdワンショットジョブとして登録する"""
import os
import plistlib
import subprocess

PYTHON = "/opt/homebrew/bin/python3"
SCRIPT = os.path.expanduser("~/projects/claude/ai-company/scripts/post_tweet.py")
PLIST_DIR = os.path.expanduser("~/Library/LaunchAgents")

posts = [
    {
        "label": "com.ichi-eigo.post-20250320-0700",
        "year": 2026, "month": 3, "day": 20, "hour": 7, "minute": 0,
        "text": "英単語を覚えたのに翌日には忘れてる。それ、あなたのせいじゃないです。人間の脳は24時間で67%を忘れるようにできている。1885年の実験で発見され、2015年の追試でも同じ結果。だから「覚えが悪い」んじゃなく「復習のタイミング」が全て。翌日にもう一回触れるだけで定着率は劇的に変わります。",
    },
    {
        "label": "com.ichi-eigo.post-20250320-1800",
        "year": 2026, "month": 3, "day": 20, "hour": 18, "minute": 0,
        "text": "スピーキング練習に使える「4/3/2」という方法があります。同じ話題を4分、3分、2分と縮めて3回話すだけ。回数を重ねるごとに発話速度が上がりポーズが減ることが研究で実証されています。相手がいなくても一人でできるのがポイント。今日の出来事を英語で話してみてください。",
    },
    {
        "label": "com.ichi-eigo.post-20250321-0700",
        "year": 2026, "month": 3, "day": 21, "hour": 7, "minute": 0,
        "text": "発音を良くしたいなら、まず「聞き分け」から始めてください。25年分の研究をまとめたメタ分析で、聞き取りトレーニングだけで発音も改善することがわかっています。効果量は0.92で、しかもその効果は数ヶ月持続する。口の形を鏡で確認するより、まず耳を鍛える方が近道です。",
    },
    {
        "label": "com.ichi-eigo.post-20250321-1800",
        "year": 2026, "month": 3, "day": 21, "hour": 18, "minute": 0,
        "text": "「語彙力が足りない」と焦って難しい単語帳に手を出すのは間違いです。研究によると、最頻出2,000語だけで英文の約80%をカバーできる。まずはこの2,000語を完璧にする方が圧倒的に効率的。小説を読むには9,000語族必要ですが、日常会話なら6,000〜7,000語族で十分です。",
    },
    {
        "label": "com.ichi-eigo.post-20250322-0700",
        "year": 2026, "month": 3, "day": 22, "hour": 7, "minute": 0,
        "text": "シャドーイングは上級者向けだと思っていませんか。実は研究で、初中級者ほど効果が大きいことがわかっています。日本人学習者43名を対象にした実験では、低レベルの学習者のリスニングスコアが最も大きく伸びました。難しく感じても大丈夫。むしろ今の段階で始めた方が得です。",
    },
    {
        "label": "com.ichi-eigo.post-20250322-1800",
        "year": 2026, "month": 3, "day": 22, "hour": 18, "minute": 0,
        "text": "1日2時間の勉強より「30分を4回」に分けた方が記憶に残ります。これは分散学習効果と呼ばれ、研究で繰り返し実証されてきました。人間の集中力は25〜30分が限界。その後は注意力が落ちて効率が下がる。短い学習を間隔を空けて繰り返す。これだけで同じ時間でも成果が変わります。",
    },
]

for p in posts:
    plist = {
        "Label": p["label"],
        "ProgramArguments": [PYTHON, SCRIPT, p["text"]],
        "StartCalendarInterval": {
            "Month": p["month"],
            "Day": p["day"],
            "Hour": p["hour"],
            "Minute": p["minute"],
        },
        "StandardOutPath": os.path.expanduser(f"~/Library/Logs/{p['label']}.log"),
        "StandardErrorPath": os.path.expanduser(f"~/Library/Logs/{p['label']}.err"),
        "EnvironmentVariables": {
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
        },
    }

    plist_path = os.path.join(PLIST_DIR, f"{p['label']}.plist")

    # Unload if already loaded
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{p['label']}"],
                    capture_output=True)

    with open(plist_path, "wb") as f:
        plistlib.dump(plist, f)

    result = subprocess.run(
        ["launchctl", "bootstrap", f"gui/{os.getuid()}", plist_path],
        capture_output=True, text=True
    )
    status = "OK" if result.returncode == 0 else f"ERR: {result.stderr.strip()}"
    print(f"{p['label']}: {p['month']}/{p['day']} {p['hour']:02d}:{p['minute']:02d} -> {status}")

print("\nDone! 6 jobs registered.")
