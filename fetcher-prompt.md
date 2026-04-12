# フェッチャープロンプト

post-history.md を読んで、まだデータを取得していない投稿の
エンゲージメントを Threads API で取得してください。

【手順】

1. post-history.md を読んで、metrics_fetched が false の投稿を特定する

2. Threads API でその投稿のデータを取得
   - エンドポイント: https://graph.threads.net/v1.0/{投稿ID}
   - 取得フィールド: ?fields=likes,replies,reposts,quotes,views
   - アクセストークンは環境変数 THREADS_ACCESS_TOKEN を使う

3. コメント（リプライ）も API で取得
   - エンドポイント: https://graph.threads.net/v1.0/{投稿ID}/replies?fields=text,timestamp
   - 取得したコメントが「質問」かどうか判定
     （「？」「教えて」「どうしたら」が含まれていたら質問）

4. 取得したデータを post-history.md の該当投稿に追記
   - いいね数、コメント数、リポスト数、閲覧数
   - コメント一覧（質問フラグつき）
   - metrics_fetched を true に変更

【注意】
- 投稿から24時間以上経ったものだけ対象にする（数字が安定するまで待つ）
- API エラーの場合は metrics_fetched を false のままにして次回再取得
