# Daily English Library

1日3回、各約400語の英語エッセイ、日本語訳、重要表現5個を読むサイトです。

| 日本時間 | 難易度 |
| --- | --- |
| 7:00 | 英検3級程度 |
| 12:00 | 英検準2級程度 |
| 17:00 | 英検2級程度 |

難易度フィルターと配信時刻表示に対応。従来記事と既読記録を保持します。

## 公開
GitHubの Settings → Pages → Build and deployment で、Source を「Deploy from a branch」、Branch を「main」、フォルダを「/ (root)」にして保存します。
公開URL: https://seikoubon.github.io/daily-english-library/

## ファイル
- `index.html`: 公開トップページ。英文、日本語訳、検索、ジャンル選択、端末内の読了記録。
- `daily_english_library.html`: 同じ内容のダウンロード用HTML。
- `daily_english_articles.json`: 全記事のJSON配列。`is_preview: true` は短縮サンプルです。

## 毎日の更新
ChatGPTの定期タスクが朝・昼・夕に、GitHubと所有者専用サイトへ独立して保存します。Google Driveへのバックアップは行いません。GitHub側で新たに英文を生成する処理やAI APIは使いません。
HTMLでは最初の `let articles=[…],idx=0` の配列だけを全記事で置換します。JSON内の `<` は `\u003c` にしてscript要素の終端を防ぎます。既存記事を保持し、正式記事は日付＋配信枠で更新します。

既存の連携ツールのスキーマを保つため、JSONのtitleは `[07:00] English Title`、`[12:00] English Title`、`[17:00] English Title` とします。サイトでは接頭辞を外してタイトルを表示し、時刻・難易度を別に表示します。キーは `article|YYYY-MM-DD|HH:MM`。接頭辞のない従来記事は `article|YYYY-MM-DD` の独立した記事として残します。サンプルのキーは日付＋タイトルです。同じ枠の再実行だけが更新となり、他の枠は保持されます。

ジャンルは2026-11-02起点の従来8日周期を維持し、同日は同ジャンルで異なる題材を3本作ります。既存の正式記事は難易度・時刻を遡って変更しません。
GitHub Pagesのブランチ公開が有効なら、コミット後に公開サイトへ反映されます。タスク設定は自動実行の成功保証ではありません。毎日の配信内でGitHub保存の結果を確認してください。

公開サイトの読了記録・手動取り込み記事は各ブラウザ内だけに保存します。所有者専用サイトのクラウド読了記録とは同期しません。


## 音声・動画とYouTube
英文から音声・SRT・MP4を生成し、任意でYouTubeへ投稿できます。途中再開・重複投稿防止に対応。
導入と認証は [音声・動画マニュアル](docs/MEDIA_GUIDE_JA.md) を参照してください。

