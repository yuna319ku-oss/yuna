# TikTok リサーチスキル

アカウントのジャンルに合わせてTikTokをリサーチし、知識ファイルを更新します。

---

## 手順

### STEP 1: アカウント情報の読み込み

`01_profile.md` と `03_genre.md` を読み込んで、このアカウントのジャンル・テーマを把握する。

### STEP 2: 検索キーワードの自動生成

ジャンルに合わせて今回調べる検索キーワードを5つ選ぶ。
- `04_domain/tiktok-research-log.md` を読んで、前回調べたキーワードは除外する
- キーワードは「新作」「流行」「ブランド名」「アイドル名 コスメ」等を組み合わせる
- 今回使うキーワード5つをユーザーに提示して確認を取る

### STEP 3: TikTok動画の収集（yt-dlp）

各キーワードについて以下を実行：

```bash
# 検索結果から直近2週間・再生数上位5本を取得
yt-dlp "ytsearch5:TikTok {キーワード}" \
  --match-filter "upload_date >= $(date -d '14 days ago' +%Y%m%d)" \
  --write-info-json \
  --skip-download \
  -o "04_domain/tiktok-cache/%(id)s.%(ext)s"
```

すでにログに記録済みの動画ID（`tiktok-research-log.md` に記載）はスキップする。

### STEP 4: 動画ダウンロード（新規分のみ）

```bash
yt-dlp {動画URL} \
  -o "04_domain/tiktok-cache/%(id)s.%(ext)s" \
  --extract-audio --audio-format mp3
```

### STEP 5: Whisperで文字起こし

```bash
whisper 04_domain/tiktok-cache/{動画ID}.mp3 \
  --language ja \
  --output_dir 04_domain/tiktok-cache/ \
  --output_format txt
```

### STEP 6: 情報の抽出・整理

文字起こしテキストとキャプション（info-jsonのdescriptionフィールド）から以下を抽出：

**抽出項目:**
- 新作コスメ・カラコン名
- 流行りの韓国コスメ・ブランド名
- おすすめ商品名・価格
- バズってる投稿の1行目パターン
- 構成パターン（型の分類）

**構成パターンの分類例:**
- 断言型：「これ買って。絶対後悔しない」
- 数字型：「3000円以下で買えるIVEリウ级リップ」
- 体験型：「使ったら翌朝肌が変わった」
- 問題提起型：「カラコン選びで失敗してた理由」

### STEP 7: ファイルへの保存

以下のファイルを更新する：

**`04_domain/cosme-trends.md`** に追記：
```
## {調査日} リサーチ結果

### 新作・注目コスメ
- 商品名：価格・特徴

### 流行りブランド
- ブランド名：特徴

### おすすめカラコン
- 商品名：価格
```

**`06_references.md`** にバズ投稿の1行目・構成パターンを追記。

**`04_domain/tiktok-research-log.md`** に今回の記録を追記：
```
## {調査日}
- 使用キーワード: xxx, xxx, xxx
- 取得動画ID: [id1, id2, ...]
- 次回候補キーワード: xxx, xxx, xxx
```

### STEP 8: 次回キーワードの提案

今回の調査で出てきた関連ワード・気になるキーワードを3〜5個提案する。

---

## 注意事項
- 1回の実行で検索キーワードは最大5つまで
- 前回取得済みの動画IDは `tiktok-research-log.md` で管理し重複取得しない
- 直近2週間以内の動画のみ対象
- 収集した知識は必ず `04_domain/` 配下に保存
- TikTokの利用規約の範囲内で実行すること
