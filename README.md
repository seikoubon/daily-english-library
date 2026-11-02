# Daily English Library

英検2級・CEFR B1程度の英語エッセイ、日本語訳、重要表現を読むサイトです。

## 公開
GitHubの Settings → Pages → Build and deployment で、Source を「Deploy from a branch」、Branch を「main」、フォルダを「/ (root)」にして保存します。
公開URL: https://seikoubon.github.io/daily-english-library/

## ファイル
- `index.html`: 公開トップページ。英文、日本語訳、検索、ジャンル選択、端末内の読了記録。
- `daily_english_library.html`: 同じ内容のダウンロード用HTML。
- `daily_english_articles.json`: 全記事のJSON配列。`is_preview: true` は短縮サンプルです。

## 毎日の更新
既存のChatGPT「毎朝の英語エッセイ」タスクが、Drive・所有者専用サイトへの保存に続いて、GitHub連携でJSONと2つのHTMLを更新します。GitHub側で新たに英文を生成する処理やAI APIは使いません。
HTMLでは最初の `let articles=[…],idx=0` の配列だけを全記事で置換します。JSON内の `<` は `\u003c` にしてscript要素の終端を防ぎます。既存記事を保持し、正式記事は日付で更新します。
GitHub Pagesのブランチ公開が有効なら、コミット後に公開サイトへ反映されます。タスク設定は自動実行の成功保証ではありません。毎日の配信内でGitHub保存の結果を確認してください。

公開サイトの読了記録・手動取り込み記事は各ブラウザ内だけに保存します。所有者専用サイトのクラウド読了記録とは同期しません。


## 音声・動画とYouTube
英文から音声・SRT・MP4を生成し、任意でYouTubeへ投稿できます。途中再開・重複投稿防止に対応。
導入と認証は [音声・動画マニュアル](docs/MEDIA_GUIDE_JA.md) を参照してください。
