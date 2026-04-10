# DESIGN.md — native-real.com

> **Design Foundation**: Lovable-inspired warm minimalism
> **Goal**: Maximum user acquisition and retention for English learners
> **Last updated**: 2026-04-06

---

## 1. Visual Theme & Atmosphere

native-real は「毎日続けたくなる英語学習の場」。デザインは学習者が長時間見ても疲れず、達成感を感じやすい暖かみのある空間を目指す。

冷たい純白ではなく、手帳のような温かいクリーム地（`#F8F6F1`）をベースにする。
テキストは純黒ではなく、わずかに温もりのある濃色（`#1A1A1A`）。
色は増やさない。ゴールド（`#F5A623`）を唯一のブランドアクセントとして維持し、それ以外はウォームニュートラルで統一する。

**設計の優先順位:**
1. 滞在時間 — 疲れない配色・読みやすいタイポグラフィ
2. 達成感 — 正解・レベルアップ・連続学習の視覚的フィードバック
3. 行動誘導 — CTAはゴールドで目を引き、タップしやすいサイズ
4. 日英両対応 — Noto Sans JP との組み合わせで崩れない

---

## 2. Color Palette & Roles

### CSS変数（`:root` に定義）

```css
:root {
  /* ── Base ── */
  --bg:           #F8F6F1;   /* ページ背景（温かみのあるクリーム） */
  --bg-elevated:  #FDFCF9;   /* カード・モーダルの背景 */
  --bg-subtle:    #F2EFE9;   /* セクション区切り・インプット背景 */

  /* ── Surface（opacity-driven） ── */
  --surface:      rgba(26,26,26,0.04);
  --surface-2:    rgba(26,26,26,0.07);
  --surface-hover:rgba(26,26,26,0.06);

  /* ── Border ── */
  --border:       #E8E4DC;   /* カード・コンテナの境界線 */
  --border-strong:rgba(26,26,26,0.35);  /* インタラクティブ要素 */

  /* ── Text ── */
  --text-1:       rgba(26,26,26,0.88);  /* 本文・見出し */
  --text-2:       rgba(26,26,26,0.62);  /* 説明文・ラベル */
  --text-3:       rgba(26,26,26,0.42);  /* プレースホルダー・補足 */

  /* ── Brand Accent ── */
  --gold:         #F5A623;              /* CTA・アクティブ状態・ブランド */
  --gold-dim:     rgba(245,166,35,0.65);
  --gold-glow:    rgba(245,166,35,0.18);
  --gold-bg:      rgba(245,166,35,0.10);

  /* ── Quiz Feedback ── */
  --success:      #16A34A;             /* 正解・達成 */
  --success-bg:   rgba(22,163,74,0.10);
  --error:        #DC2626;             /* 不正解 */
  --error-bg:     rgba(220,38,38,0.10);
  --hint:         #D97706;             /* ヒント・警告 */
  --hint-bg:      rgba(217,119,6,0.10);

  /* ── Gamification ── */
  --xp:           #F5A623;             /* XPバー・レベルアップ（ゴールドと統一） */
  --streak:       #EA580C;             /* 連続学習ストリーク */
  --streak-bg:    rgba(234,88,12,0.10);

  /* ── Interactive ── */
  --teal:         #0EA5E9;             /* セカンダリCTA・リンク */
  --teal-bg:      rgba(14,165,233,0.08);

  /* ── Shape ── */
  --radius:       14px;
  --radius-sm:    8px;
  --radius-lg:    20px;
  --radius-pill:  9999px;

  /* ── Motion ── */
  --t:            0.18s ease;
  --t-fast:       0.10s ease;
}
```

### カラーロール早見表

| 色 | Hex / rgba | 用途 |
|---|---|---|
| クリーム | `#F8F6F1` | ページ背景（必ずこれを使う・純白禁止） |
| エレベーテッド | `#FDFCF9` | カード・モーダル表面 |
| サトル | `#F2EFE9` | セクション背景・入力欄 |
| ボーダー | `#E8E4DC` | カード境界線・区切り |
| テキスト1 | `rgba(26,26,26,0.88)` | 見出し・本文 |
| テキスト2 | `rgba(26,26,26,0.62)` | 説明・ラベル |
| テキスト3 | `rgba(26,26,26,0.42)` | 補足・プレースホルダー |
| ゴールド | `#F5A623` | CTA・アクティブ・ブランドアクセント |
| 成功 | `#16A34A` | 正解・達成 |
| エラー | `#DC2626` | 不正解 |
| ヒント | `#D97706` | ヒントパネル・注意 |
| ストリーク | `#EA580C` | 連続学習バッジ |
| ティール | `#0EA5E9` | セカンダリリンク・情報アイコン |

---

## 3. Typography Rules

### フォント設定

```css
body {
  font-family: 'Inter', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

- **Inter**: 英語テキスト・数値・UIラベル
- **Noto Sans JP**: 日本語テキスト（自動フォールバック）
- フォールバック: `-apple-system, BlinkMacSystemFont`（ネイティブ優先）

### タイポグラフィスケール

| 役割 | サイズ | Weight | Line-height | Letter-spacing | 用途 |
|---|---|---|---|---|---|
| Display Hero | 48–56px | 800 | 1.05 | -1.2px | ランディングページ ヒーロー |
| Section Title | 32–36px | 700 | 1.10 | -0.8px | セクション見出し |
| Card Title | 20–24px | 700 | 1.20 | -0.4px | カード・モーダルタイトル |
| Body Large | 17–18px | 400 | 1.55 | normal | 問題文・解説文 |
| Body | 15–16px | 400 | 1.60 | normal | 本文・選択肢テキスト |
| UI Label | 14px | 600 | 1.40 | 0.2px | ボタン・タブ・バッジ |
| Caption | 12–13px | 500 | 1.40 | 0.3px | 補足・タイムスタンプ |
| Micro | 11px | 600 | 1.30 | 0.5px | バッジ内文字・大文字ラベル |

### 原則
- **見出しは必ず負のletter-spacing**: 大きいフォントほどきつく詰める（-0.4px〜-1.2px）
- **日本語見出し**: letter-spacing を 0 に戻す（日本語フォントはトラッキング不要）
- **本文**: 行間 1.55–1.60 を必ず維持（読みやすさ最優先）
- **数値・スコア表示**: `font-variant-numeric: tabular-nums` でガタつき防止

---

## 4. Component Stylings

### ボタン

**Primary CTA（ゴールド）**
```css
background: linear-gradient(135deg, #E09520 0%, #F5A623 50%, #F8C347 100%);
color: #000;
font-weight: 800;
font-size: 17px;
padding: 14px 28px;
border-radius: var(--radius-pill);
border: none;
min-height: 52px;
box-shadow: 0 2px 8px rgba(245,166,35,0.35), inset 0 1px 0 rgba(255,255,255,0.3);
```
用途: 「クイズを始める」「次の問題へ」など主要アクション

**Ghost / Secondary**
```css
background: transparent;
color: var(--text-1);
border: 1px solid var(--border-strong);
padding: 10px 20px;
border-radius: var(--radius-pill);
font-weight: 600;
font-size: 14px;
```
用途: 「スキップ」「設定」など補助アクション

**Teal Secondary CTA**
```css
background: linear-gradient(135deg, #0D9488, #0EA5E9);
color: #fff;
font-weight: 700;
padding: 12px 24px;
border-radius: var(--radius-pill);
```
用途: アフィリエイト誘導・外部リンクCTA

**Tab / カテゴリボタン（Zapier式インセット下線）**
```css
background: transparent;
color: var(--text-2);
padding: 10px 16px;
font-size: 14px;
font-weight: 600;
border: none;
transition: box-shadow 0.15s ease;

/* アクティブ状態 */
.tab.active {
  color: var(--gold);
  box-shadow: var(--gold) 0px -3px 0px 0px inset;
}

/* ホバー */
.tab:hover {
  color: var(--text-1);
  box-shadow: var(--border-strong) 0px -3px 0px 0px inset;
}
```
用途: クイズモード切り替え・カテゴリフィルター

### クイズ選択肢ボタン（quiz-specific）

```css
/* デフォルト */
.opt-btn {
  background: var(--bg-elevated);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 18px;
  min-height: 56px;
  text-align: left;
  font-size: 15px;
  color: var(--text-1);
  transition: all var(--t);
  cursor: pointer;
}
.opt-btn:hover { background: var(--surface); border-color: var(--border-strong); }

/* 正解 */
.opt-btn.correct {
  background: var(--success-bg);
  border-color: var(--success);
  color: var(--success);
}

/* 不正解 */
.opt-btn.wrong {
  background: var(--error-bg);
  border-color: var(--error);
  color: var(--error);
}

/* 選択済み（結果待ち） */
.opt-btn.selected {
  background: var(--gold-bg);
  border-color: var(--gold);
}
```

### カード・コンテナ

```css
.card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
}

/* ホバーカード */
.card-hover:hover {
  border-color: var(--border-strong);
  box-shadow: 0 4px 16px rgba(26,26,26,0.08);
}
```
- Shadow は hover / focus 時のみ使用。デフォルトはボーダーで表現する

### XP・レベルバー（gamification）

```css
.xp-bar-track {
  height: 6px;
  background: var(--surface-2);
  border-radius: var(--radius-pill);
}
.xp-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #E09520, #F5A623, #F8C347);
  border-radius: var(--radius-pill);
  transition: width 0.4s ease;
}

/* レベルバッジ */
.level-badge {
  background: var(--gold-bg);
  color: var(--gold);
  border: 1px solid rgba(245,166,35,0.3);
  border-radius: var(--radius-pill);
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 700;
}
```

### ストリークバッジ

```css
.streak-badge {
  background: var(--streak-bg);
  color: var(--streak);
  border: 1px solid rgba(234,88,12,0.25);
  border-radius: var(--radius-pill);
  padding: 4px 10px;
  font-size: 13px;
  font-weight: 700;
}
```

### ヒントパネル

```css
.hint-panel {
  background: var(--hint-bg);
  border: 1px solid rgba(217,119,6,0.3);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  color: var(--hint);
  font-size: 14px;
}
```

### Stats（数値表示）

```css
.stat-value {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -1.0px;
  color: var(--text-1);
}
.stat-label {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: var(--text-2);
}
```

### ナビゲーション（サイトヘッダー）

```css
.site-header {
  background: rgba(248,246,241,0.92);  /* クリーム背景 + blur */
  backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid var(--border);
}
.site-header-logo { color: var(--text-1); font-weight: 800; }
.site-header-nav a.active { color: var(--gold); }
.site-header-nav a.active::after {
  background: var(--gold);  /* アクティブ下線 */
}
```

---

## 5. Layout Principles

### スペーシングスケール（8px基準）

```
4px  — アイコン内余白・最小マージン
8px  — インラインギャップ
12px — コンパクト要素（バッジ・タグ）
16px — カード内余白（小）
20px — 標準パディング
24px — カード内余白（標準）
32px — コンポーネント間ギャップ
48px — セクション間（モバイル）
64px — セクション間（デスクトップ）
96px — 大セクション区切り
```

### グリッド・コンテナ

- 最大コンテンツ幅: `960px`（学習UIは `680px` 上限で読みやすさ優先）
- クイズエリア: `max-width: 680px; margin: 0 auto;`
- 選択肢グリッド: モバイル1列、タブレット以上は2列（選択肢4つ = 2×2）

### ブレークポイント

| 名称 | 幅 | 主な変化 |
|---|---|---|
| Mobile | ≤640px | 1カラム、パディング16px |
| Tablet | 641–1023px | 2カラム選択肢、余白24px |
| Desktop | 1024px+ | 2カラムレイアウト（音声カード左＋選択肢右） |
| Short screen | height ≤700px | `@media (max-height: 700px)` でパディング圧縮 |

### タッチターゲット（iOS HIG準拠）

- 選択肢ボタン: `min-height: 56px`
- プレイボタン: `min-height: 52px`
- ナビゲーションリンク: `min-height: 44px`
- モバイル上のすべてのボタン: `min-width: 44px`

---

## 6. Depth & Elevation

| レベル | 表現方法 | 用途 |
|---|---|---|
| Flat（0） | 背景色のみ | ページ地・テキストブロック |
| Bordered（1） | `1px solid var(--border)` | カード・選択肢・入力欄（デフォルト） |
| Interactive（2） | `border-color: var(--border-strong)` | ホバー・フォーカス状態 |
| Elevated（3） | `box-shadow: 0 4px 16px rgba(26,26,26,0.08)` | ホバーカード・ドロップダウン |
| Modal（4） | `box-shadow: 0 8px 32px rgba(26,26,26,0.15)` | モーダル・レベルアップトースト |
| Accent glow | `box-shadow: 0 2px 8px rgba(245,166,35,0.35)` | Primary CTAボタン |

**原則**: シャドウは段階ごとに1段ずつ上げる。カードのデフォルトにシャドウを使わない。境界線で輪郭を表現する。

---

## 7. Motion & Animation

```css
/* 標準トランジション */
transition: all var(--t);            /* 0.18s ease */
transition: all var(--t-fast);       /* 0.10s ease */

/* レベルアップトースト */
@keyframes toast-in {
  from { transform: translateY(-20px) scale(0.9); opacity: 0; }
  to   { transform: translateY(0) scale(1); opacity: 1; }
}

/* 正解時のパルス */
@keyframes correct-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(22,163,74,0.4); }
  70%  { box-shadow: 0 0 0 8px rgba(22,163,74,0); }
  100% { box-shadow: 0 0 0 0 rgba(22,163,74,0); }
}

/* XPバー伸長 */
transition: width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);  /* バウンス感 */
```

**原則**:
- ユーザー操作への反応（ホバー・クリック）: `0.10–0.18s`（速く・即座）
- UI状態変化（パネル表示・選択肢確定）: `0.18–0.25s`
- 演出系（トースト・レベルアップ・XPバー）: `0.3–0.5s`
- ループアニメーションは使わない（注意散漫になる）

---

## 8. Do's and Don'ts

### Do
- ページ背景は必ず `#F8F6F1`（クリーム）を使う。純白（`#FFFFFF`）は背景に使わない
- カードの輪郭は `1px solid var(--border)` で表現し、デフォルト状態にシャドウを使わない
- ゴールド（`#F5A623`）はCTAとアクティブ状態のみ。装飾目的での多用禁止
- テキストは `rgba(26,26,26,0.88/0.62/0.42)` の3段階で表現する
- 選択肢ボタンは `min-height: 56px` でタップしやすく保つ
- 見出しには必ず負のletter-spacingを設定する（-0.4px〜-1.2px）
- クイズ正解・不正解のフィードバックは色（success/error）＋ボーダー変化の2要素で伝える

### Don't
- 純白背景 `#FFFFFF` をページ背景に使わない
- カードのデフォルト状態にbox-shadowを使わない（hover時のみ許可）
- ゴールド以外のカラーを追加しない（必要なら既存の success/error/hint/streak を使う）
- フォントウェイト `900` を使わない（最大 `800`）
- アニメーションのdurationを `0.5s` より長くしない（重く感じる）
- タブナビゲーションにborder-bottomを使わない（`box-shadow inset` パターンを使う）
- `letter-spacing` を日本語テキストの見出しに適用しない

---

## 9. Agent Prompt Guide

### クイックカラーリファレンス

```
ページ背景:     #F8F6F1
カード背景:     #FDFCF9
セクション背景: #F2EFE9
ボーダー:      #E8E4DC
テキスト（強）: rgba(26,26,26,0.88)
テキスト（弱）: rgba(26,26,26,0.62)
ブランドアクセント: #F5A623（ゴールド）
正解色:        #16A34A
不正解色:      #DC2626
ヒント色:      #D97706
```

### コンポーネント生成プロンプト例

**クイズ選択肢（4択）**
「クリーム背景（#FDFCF9）、1.5px solid #E8E4DC のボーダー、border-radius 14px、padding 14px 18px、min-height 56px の選択肢ボタンを4つ縦並びで作成。正解時は背景 rgba(22,163,74,0.10)・ボーダー #16A34A に変化。不正解時は rgba(220,38,38,0.10)・#DC2626 に変化。ホバー時はボーダーを rgba(26,26,26,0.35) に。」

**XP/レベルバー**
「ゴールドグラデーション（#E09520 → #F5A623 → #F8C347）の6px高さのプログレスバー。背景トラックは rgba(26,26,26,0.07)。左に Lv.{n} バッジ（#F5A623 背景10%、ゴールドテキスト、pill形状）、右にXP数値（font-size 13px、rgba(26,26,26,0.62)）。」

**ランディングページ ヒーローセクション**
「背景 #F8F6F1 のヒーロー。見出し48px、font-weight 800、letter-spacing -1.2px、color rgba(26,26,26,0.88)。サブテキスト18px、weight 400、line-height 1.55、color rgba(26,26,26,0.62)。CTAボタンはゴールドグラデーション（#E09520→#F5A623→#F8C347）、黒テキスト、font-weight 800、padding 14px 28px、border-radius 9999px。」

**Stats カウンター**
「40px、font-weight 800、letter-spacing -1.0px のスコア数値。下に13px、font-weight 600、letter-spacing 0.3px、rgba(26,26,26,0.62) のラベル。横並び3つ、gap 48px。」

**セクション見出し**
「32px、font-weight 700、letter-spacing -0.8px、rgba(26,26,26,0.88)。下にサブテキスト16px、weight 400、rgba(26,26,26,0.62)。中央揃え、bottom-margin 48px。」

### 反復ガイドライン
1. 背景は常に `#F8F6F1`（クリーム）から始める
2. カードは `#FDFCF9` + `1px solid #E8E4DC` のボーダーで輪郭を作る
3. アクセントはゴールド1色。正解・不正解・ヒントは専用色を使う
4. 見出しのletter-spacingは必ずマイナス値（-0.4〜-1.2px）
5. ボタンは全て `border-radius: 9999px`（pill）か `14px` のいずれか
6. シャドウはhover/モーダルにのみ使用。デフォルト状態には使わない
7. タブのアクティブ状態は `box-shadow: var(--gold) 0px -3px 0px 0px inset` で表現
