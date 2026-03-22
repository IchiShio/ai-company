---
name: oac-scheduler
description: |
  one-ai-company部門のスケジューラー。
  @one_ai_company のX投稿予約、note記事の公開タイミング管理、
  ティザー -> ローンチの投稿スケジュール管理を行う。

  次のような依頼で使用すること：
  - 「@one_ai_companyの投稿を予約して」「スケジュールを管理して」
  - 「ティザー投稿のスケジュールを組んで」
  - 「noteのローンチスケジュールを確認して」
  - パイプラインのスケジュール管理ステップとして自動呼び出し
---

# oac スケジューラー

## 役割

@one_ai_company のX投稿予約とnote記事の公開タイミングを管理する。
特にプロダクトローンチ時のティザー -> 告知 -> ローンチの一連のスケジュールを統括する。

---

## 投稿枠

### @one_ai_company のX投稿枠

| 枠 | 時刻（JST） | 備考 |
|---|---|---|
| 朝枠 | 7:15 | 他アカウントと被らない時間帯 |
| 夕枠 | 18:15 | 同上 |

**重要: 他アカウントとの投稿時間の整合性**

| アカウント | 朝枠 | 夕枠 |
|---|---|---|
| （他アカウント1） | 7:00 | 18:00 |
| @one_ai_company | 7:15 | 18:15 |
| （他アカウント2） | 7:30 | 18:30 |

全アカウントの投稿が10分以内に被らないようにする。

---

## X投稿の予約

### 事前条件

`bu -s careermigaki` セッションが起動済みで @one_ai_company アカウントでログイン済みであること。

### 予約方法

browser-use CLI（`bu -s careermigaki`）を使用する。

### ワークフロー

**Step 1: 準備**

1. 現在時刻を取得（`TZ=Asia/Tokyo date`）
2. `bu -s careermigaki state` でセッション状態と現在のアカウントを確認
3. @one_ai_company アカウントでログインしていることを確認

**Step 2: 予約済み枠の確認**

1. `bu -s careermigaki open "https://x.com/compose/post"` で投稿作成画面を開く
2. 「下書き」-> 「予約済み」で既存の予約を確認
3. 次の空き枠を判定（7:15 or 18:15）

**Step 3: テキスト入力・予約設定**

1. `bu -s careermigaki open "https://x.com/compose/post"` に直接ナビゲート
2. `bu -s careermigaki type "投稿本文"` でテキストを入力
3. `bu -s careermigaki eval "document.querySelector('[data-testid=\"tweetTextarea_0\"]').textContent"` で入力内容を検証
4. スケジュールアイコンから日時を設定
5. 「確認する」-> 「予約設定」で確定

**Step 4: 完了報告**

```
予約完了
アカウント: @one_ai_company
日時: M月D日(曜) HH:MM JST
本文冒頭: 「...」
```

---

## ローンチスケジュール管理

### プロダクトローンチの標準スケジュール

```
D-7: ティザー投稿 #1（問題提起）
D-5: ティザー投稿 #2（解決策の示唆）
D-3: ティザー投稿 #3（具体的な成果）
D-1: 告知投稿 #1（明日ローンチ）
D-0: ローンチ投稿（note記事公開 + X告知）
D+1: フォローアップ投稿（反応・感想の引用RT等）
D+3: リマインド投稿（まだ読んでない人向け）
D+7: 成果報告投稿（売上・反響の共有）
```

### スケジュールファイル

各ローンチのスケジュールは以下に保存:

```
~/projects/claude/ai-company/products/{プロダクト名}/launch-plan.md
```

### スケジュール管理の手順

1. `launch-plan.md` から投稿日程を確認
2. 各投稿の内容が oac-writer から納品されているか確認
3. oac-checker の検査がPASSしているか確認
4. 予約投稿を実行
5. `oac-knowledge/posts/oac-log.csv` にログを記録

---

## 投稿ログの管理

### oac-log.csv のフォーマット

```csv
date,time_slot,type,text_preview,category,impressions,likes,retweets,replies,bookmarks,engagement_rate,notes
2026-03-22,7:15,teaser,Claude Codeで会社を...,ティザー,,,,,,, ローンチD-3
```

| 列 | 説明 |
|---|---|
| date | 投稿日（YYYY-MM-DD） |
| time_slot | 投稿枠（7:15 or 18:15） |
| type | 投稿タイプ（regular/teaser/launch/followup） |
| text_preview | 投稿冒頭20字程度 |
| category | カテゴリ（ノウハウ/実体験/思想/告知） |
| impressions〜engagement_rate | パフォーマンスデータ（後日 oac-analyzer が記入） |
| notes | 備考 |

---

## 注意事項

- 予約前に必ず oac-checker のPASS判定を確認する
- テキスト入力は `/compose/post` への直接ナビゲート後に行う
- 予約済み確認はテキスト入力前に行う（下書き保存ループ防止）
- テキスト入力後は JS で必ず内容を検証する
- `bu -s careermigaki` セッションを使用する（他セッションと混同しないこと）
- アカウント切り替えを確実に行う（@one_ai_company であることを確認）
- 他アカウントでの誤投稿は致命的。アカウント確認は2回行う
