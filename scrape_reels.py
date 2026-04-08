#!/usr/bin/env python3
"""
Instagram Korean Cosmetics Reels Analysis
- Search for reels with specific hashtags
- Download with yt-dlp
- Transcribe with Whisper
- Extract trending cosmetics info
- Analyze caption patterns
"""

import subprocess
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# ── Configuration ──
SEARCH_QUERIES = ["韓国コスメ", "韓国メイク", "韓国アイドル"]
REELS_PER_QUERY = 5
OUTPUT_DIR = Path("/home/user/yuna/downloads")
RESULTS_FILE = Path("/home/user/yuna/analysis_report.md")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def search_instagram_hashtag(query: str, count: int = 5) -> list[dict]:
    """
    Use instaloader to fetch posts from a hashtag.
    Falls back to yt-dlp search if instaloader fails.
    """
    import instaloader

    L = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    # Convert query to hashtag format (remove #)
    hashtag_name = query.replace("#", "").replace("＃", "")

    results = []
    try:
        print(f"  Searching #{hashtag_name} via instaloader...")
        hashtag = instaloader.Hashtag.from_name(L.context, hashtag_name)

        collected = 0
        for post in hashtag.get_top_posts():
            if collected >= count:
                break
            if post.is_video:
                results.append({
                    "shortcode": post.shortcode,
                    "url": f"https://www.instagram.com/reel/{post.shortcode}/",
                    "caption": post.caption or "",
                    "likes": post.likes,
                    "video_view_count": post.video_view_count or 0,
                    "owner": post.owner_username,
                    "date": str(post.date),
                    "hashtag": hashtag_name,
                })
                collected += 1
                print(f"    Found reel: {post.shortcode} (views: {post.video_view_count})")

        if not results:
            # Try recent posts if no top posts found
            for post in hashtag.get_posts():
                if collected >= count:
                    break
                if post.is_video:
                    results.append({
                        "shortcode": post.shortcode,
                        "url": f"https://www.instagram.com/reel/{post.shortcode}/",
                        "caption": post.caption or "",
                        "likes": post.likes,
                        "video_view_count": post.video_view_count or 0,
                        "owner": post.owner_username,
                        "date": str(post.date),
                        "hashtag": hashtag_name,
                    })
                    collected += 1
                    print(f"    Found reel: {post.shortcode} (views: {post.video_view_count})")

    except Exception as e:
        print(f"  instaloader failed for #{hashtag_name}: {e}")

    return results


def search_via_web_scraping(query: str, count: int = 5) -> list[dict]:
    """
    Alternative: use yt-dlp's Instagram search capability.
    """
    results = []
    hashtag = query.replace("#", "").replace("＃", "")
    url = f"https://www.instagram.com/explore/tags/{hashtag}/"

    try:
        print(f"  Trying yt-dlp for #{hashtag}...")
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--playlist-items", f"1:{count}",
            "--no-download",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                try:
                    data = json.loads(line)
                    results.append({
                        "shortcode": data.get("id", ""),
                        "url": data.get("url", data.get("webpage_url", "")),
                        "caption": data.get("description", ""),
                        "likes": data.get("like_count", 0),
                        "video_view_count": data.get("view_count", 0),
                        "owner": data.get("uploader", ""),
                        "date": data.get("upload_date", ""),
                        "hashtag": hashtag,
                    })
                except json.JSONDecodeError:
                    continue
        else:
            print(f"    yt-dlp returned: {result.stderr[:200] if result.stderr else 'no output'}")
    except Exception as e:
        print(f"    yt-dlp search failed: {e}")

    return results


def download_reel(url: str, output_dir: Path, shortcode: str) -> str | None:
    """Download a reel using yt-dlp, return the file path."""
    output_path = output_dir / f"{shortcode}.%(ext)s"
    cmd = [
        "yt-dlp",
        "-o", str(output_path),
        "--write-description",
        "--write-info-json",
        "--no-playlist",
        "--retries", "3",
        url,
    ]

    try:
        print(f"  Downloading {shortcode}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            # Find the downloaded file
            for f in output_dir.glob(f"{shortcode}.*"):
                if f.suffix in (".mp4", ".webm", ".mkv"):
                    print(f"    Downloaded: {f.name}")
                    return str(f)
        else:
            print(f"    Download failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"    Download error: {e}")

    return None


def transcribe_audio(video_path: str) -> str:
    """Transcribe video audio using Whisper."""
    import whisper

    print(f"  Transcribing {Path(video_path).name}...")
    try:
        model = whisper.load_model("base")
        result = model.transcribe(video_path, language="ja")
        text = result.get("text", "").strip()
        print(f"    Transcription: {text[:100]}...")
        return text
    except Exception as e:
        print(f"    Transcription error: {e}")
        return ""


def extract_cosmetics_info(transcription: str, caption: str) -> dict:
    """Extract cosmetics-related information from text."""
    combined = transcription + "\n" + caption

    # Common Korean cosmetics brand patterns
    brand_patterns = [
        r"(?:CLIO|クリオ|clio)",
        r"(?:rom&nd|ロムアンド|romand)",
        r"(?:TIRTIR|ティルティル)",
        r"(?:AMUSE|アミューズ)",
        r"(?:MISSHA|ミシャ)",
        r"(?:innisfree|イニスフリー)",
        r"(?:ETUDE|エチュード)",
        r"(?:3CE|スリーシーイー)",
        r"(?:LANEIGE|ラネージュ)",
        r"(?:peripera|ペリペラ)",
        r"(?:NAMING|ネーミング)",
        r"(?:dasique|デイジーク)",
        r"(?:JUNG SAEM MOOL|ジョンセンムル)",
        r"(?:hince|ヒンス)",
        r"(?:WAKEMAKE|ウェイクメイク)",
        r"(?:espoir|エスポア)",
        r"(?:MUZIGAE MANSION|ムジガエマンション)",
        r"(?:TOO COOL FOR SCHOOL|トゥークールフォースクール)",
        r"(?:VT|ブイティー)",
        r"(?:SKIN1004|スキンサウザンドフォー)",
        r"(?:COSRX|コスアールエックス)",
        r"(?:Sulwhasoo|ソルファス)",
        r"(?:Dr\.Jart|ドクタージャルト)",
        r"(?:BANILA CO|バニラコ)",
        r"(?:MERZY|マージー)",
        r"(?:UNLEASHIA|アンリシア)",
        r"(?:CELEFIT|セレフィット)",
        r"(?:TOCOBO|トコボ)",
        r"(?:Beauty of Joseon|ビューティーオブジョセオン)",
        r"(?:Anua|アヌア)",
        r"(?:medicube|メディキューブ)",
        r"(?:BIODANCE|バイオダンス)",
    ]

    # Price patterns
    price_patterns = [
        r"(\d{3,5}\s*円)",
        r"(¥\s*\d{3,5})",
        r"(\d{1,2},\d{3}\s*円)",
        r"(₩\s*[\d,]+)",
    ]

    # Product categories
    category_keywords = {
        "リップ": ["リップ", "ティント", "グロス", "口紅"],
        "ファンデーション": ["ファンデ", "クッション", "ベース"],
        "アイシャドウ": ["アイシャドウ", "パレット", "アイカラー"],
        "スキンケア": ["美容液", "セラム", "化粧水", "トナー", "クリーム", "パック", "マスク"],
        "チーク": ["チーク", "ブラッシュ"],
        "マスカラ": ["マスカラ"],
        "コンシーラー": ["コンシーラー"],
        "下地": ["下地", "プライマー"],
    }

    found_brands = []
    for pattern in brand_patterns:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        found_brands.extend(matches)

    found_prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, combined)
        found_prices.extend(matches)

    found_categories = {}
    for cat, keywords in category_keywords.items():
        for kw in keywords:
            if kw in combined:
                found_categories[cat] = found_categories.get(cat, [])
                found_categories[cat].append(kw)

    # Check for "new" / "新作" indicators
    is_new = any(kw in combined for kw in ["新作", "新色", "新発売", "NEW", "new", "限定", "春新作", "2024", "2025", "2026"])
    is_expert = any(kw in combined for kw in ["プロ", "メイクさん", "スタイリスト", "美容部員", "専門家", "ヘアメイク", "BA"])
    is_trending = any(kw in combined for kw in ["バズ", "話題", "人気", "トレンド", "流行", "売り切れ", "即完売"])

    return {
        "brands": list(set(found_brands)),
        "prices": list(set(found_prices)),
        "categories": found_categories,
        "is_new_product": is_new,
        "is_expert_recommendation": is_expert,
        "is_trending": is_trending,
    }


def analyze_caption_patterns(all_reels: list[dict]) -> dict:
    """Analyze caption patterns across all collected reels."""
    first_lines = []
    patterns = {
        "question_start": 0,
        "emoji_start": 0,
        "brand_name_start": 0,
        "exclamation_start": 0,
        "hashtag_heavy": 0,
        "call_to_action": 0,
    }

    for reel in all_reels:
        caption = reel.get("caption", "")
        if not caption:
            continue

        lines = caption.strip().split("\n")
        first_line = lines[0].strip() if lines else ""
        first_lines.append({
            "line": first_line,
            "views": reel.get("video_view_count", 0),
            "owner": reel.get("owner", ""),
        })

        # Classify patterns
        if "?" in first_line or "？" in first_line:
            patterns["question_start"] += 1
        if re.match(r"^[\U0001F300-\U0001FAFF]", first_line):
            patterns["emoji_start"] += 1
        if "!" in first_line or "！" in first_line:
            patterns["exclamation_start"] += 1
        if caption.count("#") > 10:
            patterns["hashtag_heavy"] += 1
        if any(kw in caption for kw in ["保存して", "フォロー", "いいね", "コメント", "シェア", "プロフ"]):
            patterns["call_to_action"] += 1

    return {
        "first_lines": first_lines,
        "patterns": patterns,
        "total_analyzed": len(first_lines),
    }


def generate_report(all_reels: list[dict], transcriptions: dict, extractions: dict, caption_analysis: dict) -> str:
    """Generate the final analysis report in Markdown."""

    report = []
    report.append("# Instagram 韓国コスメ リール分析レポート")
    report.append(f"\n**分析日**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    report.append(f"**検索キーワード**: {', '.join(SEARCH_QUERIES)}")
    report.append(f"**収集リール数**: {len(all_reels)}本")

    # ── Section 1: Collected Reels Summary ──
    report.append("\n---\n## 1. 収集したリール一覧\n")

    for query in SEARCH_QUERIES:
        reels = [r for r in all_reels if r.get("hashtag") == query.replace("#", "").replace("＃", "")]
        if not reels:
            reels = [r for r in all_reels if r.get("hashtag") == query]
        report.append(f"\n### #{query}\n")

        if not reels:
            report.append("（該当リールなし）\n")
            continue

        # Sort by views
        reels.sort(key=lambda x: x.get("video_view_count", 0), reverse=True)

        for i, reel in enumerate(reels, 1):
            report.append(f"**{i}. @{reel.get('owner', '不明')}**")
            report.append(f"- URL: {reel.get('url', 'N/A')}")
            report.append(f"- 再生数: {reel.get('video_view_count', 0):,}")
            report.append(f"- いいね数: {reel.get('likes', 0):,}")
            report.append(f"- 投稿日: {reel.get('date', 'N/A')}")
            caption_preview = (reel.get("caption", "") or "")[:150].replace("\n", " ")
            report.append(f"- キャプション冒頭: {caption_preview}")
            report.append("")

    # ── Section 2: Transcriptions ──
    report.append("\n---\n## 2. 音声文字起こし\n")

    for shortcode, text in transcriptions.items():
        reel = next((r for r in all_reels if r.get("shortcode") == shortcode), {})
        report.append(f"### {shortcode} (@{reel.get('owner', '不明')})")
        report.append(f"```\n{text if text else '（文字起こし失敗または無音）'}\n```\n")

    # ── Section 3: Trending Korean Cosmetics ──
    report.append("\n---\n## 3. 最近流行りの韓国コスメ\n")

    trending_brands = set()
    trending_items = []
    for sc, info in extractions.items():
        if info.get("is_trending"):
            trending_brands.update(info.get("brands", []))
            reel = next((r for r in all_reels if r.get("shortcode") == sc), {})
            trending_items.append({
                "shortcode": sc,
                "brands": info.get("brands", []),
                "categories": info.get("categories", {}),
                "source": reel.get("owner", ""),
            })

    if trending_brands:
        report.append("### トレンドブランド")
        for brand in sorted(trending_brands):
            report.append(f"- {brand}")
    else:
        report.append("（明確なトレンド言及なし）")
    report.append("")

    # ── Section 4: New Products ──
    report.append("\n---\n## 4. 新作韓国コスメ\n")

    new_items = []
    for sc, info in extractions.items():
        if info.get("is_new_product"):
            reel = next((r for r in all_reels if r.get("shortcode") == sc), {})
            new_items.append({
                "shortcode": sc,
                "brands": info.get("brands", []),
                "categories": info.get("categories", {}),
                "prices": info.get("prices", []),
                "source": reel.get("owner", ""),
                "caption": reel.get("caption", "")[:200],
            })

    if new_items:
        for item in new_items:
            report.append(f"- **{', '.join(item['brands']) if item['brands'] else '不明ブランド'}**")
            if item["categories"]:
                report.append(f"  - カテゴリ: {', '.join(item['categories'].keys())}")
            if item["prices"]:
                report.append(f"  - 価格: {', '.join(item['prices'])}")
            report.append(f"  - 情報源: @{item['source']}")
    else:
        report.append("（新作情報の言及なし）")
    report.append("")

    # ── Section 5: Expert Recommendations ──
    report.append("\n---\n## 5. 専門家のおすすめ\n")

    expert_items = []
    for sc, info in extractions.items():
        if info.get("is_expert_recommendation"):
            reel = next((r for r in all_reels if r.get("shortcode") == sc), {})
            expert_items.append({
                "shortcode": sc,
                "brands": info.get("brands", []),
                "source": reel.get("owner", ""),
                "caption": reel.get("caption", "")[:200],
            })

    if expert_items:
        for item in expert_items:
            report.append(f"- **@{item['source']}** のおすすめ")
            if item["brands"]:
                report.append(f"  - ブランド: {', '.join(item['brands'])}")
            report.append(f"  - 内容: {item['caption'][:100]}")
    else:
        report.append("（専門家による推薦の言及なし）")
    report.append("")

    # ── Section 6: Product Names & Prices ──
    report.append("\n---\n## 6. コスメ商品名・価格一覧\n")

    all_brands = set()
    all_prices = []
    for sc, info in extractions.items():
        all_brands.update(info.get("brands", []))
        for price in info.get("prices", []):
            reel = next((r for r in all_reels if r.get("shortcode") == sc), {})
            all_prices.append({"price": price, "source": reel.get("owner", ""), "shortcode": sc})

    if all_brands:
        report.append("### 言及されたブランド")
        for brand in sorted(all_brands):
            report.append(f"- {brand}")
        report.append("")

    if all_prices:
        report.append("### 言及された価格")
        for p in all_prices:
            report.append(f"- {p['price']} (by @{p['source']})")
    else:
        report.append("（価格情報の言及なし）")
    report.append("")

    # ── Section 7: Caption Analysis ──
    report.append("\n---\n## 7. キャプション分析（バズ投稿の構成パターン）\n")

    report.append("### 投稿1行目の一覧\n")
    if caption_analysis.get("first_lines"):
        sorted_lines = sorted(caption_analysis["first_lines"], key=lambda x: x.get("views", 0), reverse=True)
        for fl in sorted_lines:
            report.append(f"- [{fl.get('views', 0):,}再生] @{fl.get('owner', '')}: 「{fl.get('line', '')}」")

    report.append("\n### 構成パターン分析\n")
    patterns = caption_analysis.get("patterns", {})
    total = caption_analysis.get("total_analyzed", 1)
    report.append(f"- 質問形で始まる投稿: {patterns.get('question_start', 0)}/{total}")
    report.append(f"- 絵文字で始まる投稿: {patterns.get('emoji_start', 0)}/{total}")
    report.append(f"- 感嘆符で始まる投稿: {patterns.get('exclamation_start', 0)}/{total}")
    report.append(f"- ハッシュタグ多用(10個以上): {patterns.get('hashtag_heavy', 0)}/{total}")
    report.append(f"- CTA(保存・フォロー誘導)あり: {patterns.get('call_to_action', 0)}/{total}")
    report.append("")

    # ── Section 8: Full Captions ──
    report.append("\n---\n## 8. キャプション全文\n")

    for reel in all_reels:
        report.append(f"### {reel.get('shortcode', '')} (@{reel.get('owner', '不明')})")
        report.append(f"```\n{reel.get('caption', '（キャプションなし）')}\n```\n")

    # ── Section 9: Additional Keywords ──
    report.append("\n---\n## 9. 追加調査キーワード\n")

    additional_keywords = set()
    for reel in all_reels:
        caption = reel.get("caption", "")
        # Extract hashtags
        hashtags = re.findall(r"#(\w+)", caption)
        for tag in hashtags:
            if any(kw in tag for kw in ["韓国", "コスメ", "メイク", "リップ", "ティント", "スキンケア", "美容"]):
                if tag not in ["韓国コスメ", "韓国メイク", "韓国アイドル"]:
                    additional_keywords.add(tag)

    if additional_keywords:
        report.append("キャプションから発見された関連キーワード:\n")
        for kw in sorted(additional_keywords):
            report.append(f"- #{kw}")
    else:
        report.append("（追加キーワードなし）")

    return "\n".join(report)


def main():
    print("=" * 60)
    print("Instagram 韓国コスメ リール分析ツール")
    print("=" * 60)

    all_reels = []

    # ── Step 1: Search & Collect Reels ──
    print("\n[Step 1] リール検索中...")
    for query in SEARCH_QUERIES:
        print(f"\n🔍 検索: {query}")

        # Try instaloader first
        reels = search_instagram_hashtag(query, count=REELS_PER_QUERY)

        # Fallback to yt-dlp
        if not reels:
            reels = search_via_web_scraping(query, count=REELS_PER_QUERY)

        if not reels:
            print(f"  ⚠ {query} のリールが取得できませんでした")

        all_reels.extend(reels)

    print(f"\n✅ 合計 {len(all_reels)} 本のリールを収集")

    if not all_reels:
        print("\n⚠ リールが1本も取得できませんでした。")
        print("Instagram のログインが必要か、レート制限に達した可能性があります。")
        print("代替手段としてサンプルデータで分析レポートを生成します。")

        # Generate report with whatever we have
        transcriptions = {}
        extractions = {}
        caption_analysis = analyze_caption_patterns(all_reels)

        report = generate_report(all_reels, transcriptions, extractions, caption_analysis)
        RESULTS_FILE.write_text(report, encoding="utf-8")
        print(f"\n📄 レポート保存先: {RESULTS_FILE}")
        return

    # ── Step 2: Download Reels ──
    print("\n[Step 2] リールをダウンロード中...")
    downloaded = {}
    for reel in all_reels:
        sc = reel.get("shortcode", "")
        url = reel.get("url", "")
        if sc and url:
            filepath = download_reel(url, OUTPUT_DIR, sc)
            if filepath:
                downloaded[sc] = filepath

    print(f"\n✅ {len(downloaded)} 本のリールをダウンロード完了")

    # ── Step 3: Transcribe Audio ──
    print("\n[Step 3] 音声文字起こし中...")
    transcriptions = {}
    for sc, filepath in downloaded.items():
        text = transcribe_audio(filepath)
        transcriptions[sc] = text

    print(f"\n✅ {len(transcriptions)} 本の文字起こし完了")

    # ── Step 4: Extract Cosmetics Info ──
    print("\n[Step 4] コスメ情報抽出中...")
    extractions = {}
    for reel in all_reels:
        sc = reel.get("shortcode", "")
        caption = reel.get("caption", "")
        transcription = transcriptions.get(sc, "")
        info = extract_cosmetics_info(transcription, caption)
        extractions[sc] = info

        if info["brands"]:
            print(f"  {sc}: ブランド={info['brands']}")

    # ── Step 5: Analyze Caption Patterns ──
    print("\n[Step 5] キャプション分析中...")
    caption_analysis = analyze_caption_patterns(all_reels)

    # ── Step 6: Generate Report ──
    print("\n[Step 6] レポート生成中...")
    report = generate_report(all_reels, transcriptions, extractions, caption_analysis)

    RESULTS_FILE.write_text(report, encoding="utf-8")
    print(f"\n📄 レポート保存先: {RESULTS_FILE}")

    # Also save raw data as JSON
    raw_data = {
        "reels": all_reels,
        "transcriptions": transcriptions,
        "extractions": extractions,
        "caption_analysis": caption_analysis,
    }
    raw_file = Path("/home/user/yuna/raw_data.json")
    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📄 生データ保存先: {raw_file}")

    print("\n" + "=" * 60)
    print("分析完了!")
    print("=" * 60)


if __name__ == "__main__":
    main()
