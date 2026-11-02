# 英文の音声・動画制作とYouTube投稿

2026-11-02 実装。既存の公開記事JSONから、正式記事の英文だけを読み上げます。記事配信・Driveバックアップとは独立しています。

## Windowsでの準備

リポジトリをダウンロード・展開し、そのフォルダでPowerShellを開きます。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements-media.txt
winget install Gyan.FFmpeg
```

FFmpeg導入後はPowerShellを開き直してください。

## 最初の1本

```powershell
.\.venv\Scripts\python.exe scripts/english_media.py render --date 2026-11-02
```

`media/2026-11-02/` に英文、男性声MP3、英語SRT、1920×1080 MP4、制作状態を保存します。背景は濃紺です。標準の動画には字幕を焼き込まず、YouTube投稿時に切替可能な英語字幕を登録します。PCで字幕付き確認するにはVLC等でMP4と同名ではないSRTを手動選択してください。

焼き込み版が必要なら `--burn-subtitles --output media-burned` を追加してください。声は `--voice en-US-JennyNeural` 等、速度は `--rate=-15%` で変更できます。同じ保存先で原稿・声・速度・字幕設定が変わると停止するため、別の `--output` を指定します。英文の言い換え・要約は行いません。

## YouTube認証と投稿

1. Google CloudでYouTube Data API v3を有効化。
2. OAuth同意画面を設定。個人テストの場合は自分をテストユーザーに登録。
3. OAuthクライアントを「デスクトップアプリ」で作成。
4. ダウンロードしたJSONを `secrets/client_secrets.json` に配置。
5. 次を実行し、ブラウザで自分のプロジェクトと権限を確認して認証。

```powershell
.\.venv\Scripts\python.exe scripts/english_media.py auth
.\.venv\Scripts\python.exe scripts/english_media.py publish --date 2026-11-02
```

初期設定は非公開。公開する場合は `--privacy public`、限定公開は `--privacy unlisted` を明示します。投稿済み動画の公開範囲をこの引数で変更する処理はありません。YouTube Studioで変更してください。

切替字幕の登録に必要な `youtube.force-ssl` 権限を使用します。テスト中の外部OAuthアプリでは更新トークンが原則7日で失効するため、継続運用前に同意画面の公開ステータス・必要な手続きを確認してください。認証更新失敗時は無人実行を停止し、`auth`で再認証します。

edge-ttsはMicrosoft Edgeオンライン音声サービスを利用する第三者製ツールです。永続無料・稼働保証はありません。公開利用条件は別途確認してください。

## 毎日の実行

```powershell
powershell.exe -NoProfile -File scripts/daily-media.ps1
# 制作と投稿を行う場合
powershell.exe -NoProfile -File scripts/daily-media.ps1 -Publish
```

日付省略時は最新の正式記事を選び、短縮サンプルは無視します。当日記事がまだ無い場合は既存記事を再利用し、保存済み動画IDがあれば再投稿しません。

Windowsタスクスケジューラで毎朝7:30など記事公開後に実行します。プログラムを `powershell.exe`、引数を `-NoProfile -File "C:\実際の展開先\scripts\daily-media.ps1" -Publish`、開始フォルダを展開先に設定してください。「新しいインスタンスを開始しない」を選びます。時刻はPCのローカル設定に従います。PCとネット接続が必要です。本作業では利用者PCへのタスク登録は行っていません。

## 障害と復旧

- 音声失敗：最大3回再試行。完成済み工程は再利用。
- アップロード：通信中は同じ再開可能リクエストを最大5回再試行。
- 投稿結果不明：二重投稿防止のため自動再投稿を停止。YouTube Studioで確認し、動画があれば `publish --date YYYY-MM-DD --adopt-video-id 動画ID` で登録・字幕処理を再開。字幕処理失敗だけなら通常のpublish再実行で復旧。
- 動画が確実に存在しない場合のみ、バックアップ後に該当日のstate.jsonの `upload_started` をfalseにして再試行。応答不明のまま状態を削除しない。
- 強制終了後の.lock：他プロセスが動いていないことを確認して削除。
- メディアとstate.jsonはセットで保存。履歴を失うと重複投稿防止が働きません。複数PCから同じ記事を投稿しないでください。
- 認証情報・生成物は.gitignoreで除外。secretsフォルダをGitHubやDriveの公開領域に置かないでください。

## 検証の範囲

記事選択、途中再開、改訂検出、投稿結果不明時の停止は自動テストで検証します。実際のMicrosoft音声サービス接続、Google OAuth、YouTube投稿は別途実機確認が必要です。

公式・実装資料:
- https://github.com/rany2/edge-tts
- https://developers.google.com/identity/protocols/oauth2
- https://developers.google.com/youtube/v3/docs/captions/insert
- https://developers.google.com/youtube/v3/docs/videos/insert
