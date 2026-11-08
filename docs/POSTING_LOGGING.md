# 英語エッセイ投稿の段階ログ v1

## 保存先
- 実行ログ: ops/posting-runs/YYYY-MM-DD/HHMM/<attempt_id>.json
- 枠不明: ops/posting-runs/unresolved/<attempt_id>.json
- 生成本文: ops/posting-drafts/YYYY-MM-DD/HHMM/<attempt_id>.json
- attempt_id は実行ごとに作るUUID。提供されたプラットフォームrun_idは別項目で保持し、取得不能ならnull。再試行も別attemptとし、既存ログを上書きしない。
- 公開リポジトリなのでログは公開される。記事内容、公開URL、時刻、状態、公開コミットSHA、秘密値を除いたエラー要旨だけを書く。認証値・ヘッダー・環境変数・私的な会話・所有者識別情報は保存しない。

## 必須手順
起動直後、画像生成や記事取得に先立ち小さいstartedログをGitHubへ保存する。まずscheduled_for（取得できた値のみ）と実際のstarted_atを記録する。対象枠が未確定ならunresolvedへ保存し、確定後も同じファイルを使ってtargetを追記する。
下記各段階に入る前にstartedを永続保存し、結果が分かったらsucceeded / failed / skipped / unknownを保存する。前段階の終了と次段階の開始は一回のログ更新にまとめてよい。未実行はnot_started。実際の成功なしに状態を進めない。ログは最後にまとめて書くのではなく逐次保存する。

| stage | 確認内容 |
|---|---|
| resolve_slot | 予定日時、対象日・枠、判定根拠 |
| read_sources | GitHubと専用サイトそれぞれの取得成否、既存記事の有無 |
| prepare_text | 新規生成か再利用か、タイトル、英文語数、訳と語彙5個の有無 |
| persist_draft | 確定した記事JSONを生成本文パスへ保存・読み戻し |
| github_text | 記事JSONと両HTMLの保存・読み戻し、コミットSHA |
| owner_text | 専用サイトへの本文同期・読み戻し |
| image_generate | 画像生成開始・完了・再利用、出力取得手段の有無 |
| image_file | 実ファイル取得、形式、バイト数、掲載用圧縮結果 |
| github_image | 画像と画像項目付き記事の保存・読み戻し、SHAと公開画像URL |
| owner_image | 専用サイトへの画像項目同期・読み戻し |
| public_verify | 配備結果、公開HTML本文一致、画像HTTP応答・実画像確認 |
| report | チャットへ返す本文・訳・語彙と結果の準備。通知配達はunknown |

各stageにstarted_at, finished_at（実測ISO時刻。取得不能はnull）, status, evidence, errorを持たせる。errorはtool, codeまたはHTTP status, message（秘密値を除き500文字以内）, retry_count, outcome_knownを記録。非同期処理の開始だけで成功にしない。
read_sources、public_verifyなど複数対象がある段階はevidence内で対象別に結果を持つ。一般的なUnknown errorしかない場合、その文字列のみ記録し原因を推測しない。
トップレベルはschema_version:1, attempt_id, platform_run_id, invocation_kind, scheduled_for, started_at, finished_at, target:{date,slot,resolution}, status, last_completed_stage, stages, draft_path, logging_errors。
終了statusはcompleted / partial / failed。completedは本文・画像の両保存先と公開確認が成功した場合だけ。最終段階reportは配達成功を意味しない。
途中のstartedが残っていても現在稼働中とは断定せず「この段階の完了記録なし」と読む。外部変更直後に停止している可能性があるため、再実行時は保存先を読み戻してから再送する。

## 本文を失わない
prepare_textの直後に新規生成・再利用の別と語数をログ保存し、画像処理前に記事JSONをpersist_draftとして保存する。原稿の保存は公開サイトへの掲載とは別である。再実行時に同枠のGitHub公開用JSONを最優先し、専用サイト、保存原稿の順で確認する。複数の異なる本文があれば勝手に統合・上書きしない。
原稿・ログの保存に失敗しても通常の投稿やもう一方の保存先を止めない。確認可能な失敗情報をチャットにも残す。ログ失敗を無制限に再試行しない（読み戻し確認後の一時障害だけ最大1回）。接続・認証・承認要求には既定の停止規則を適用する。

## GitHub更新の競合防止
ログ作成はcreate_file、更新はfetch_fileの最新blob SHAを使ったupdate_file。実行ごとに独立したパスを使う。
ログの保存もmainを進める。記事のtree/commitを作る直前に最新head/treeを取り直す。記事のhead取得からupdate_refまではログを別コミットしない。途中にログ更新が入った場合はheadを取り直す。force pushは禁止。
画像は可能なら掲載用JPEGに変換して数百KB程度にし、実形式を検証する。原本と別ファイルにする。

## 再開と限界
次回は直近の未完了ログを少数（最大3件）読み、対象枠の本文・画像の実在状況を照合して報告する。今回の投稿を優先し、無制限な過去一括再投稿はしない。
最終報告には段階別の結果、最後の成功段階、失敗したツールと要旨、原稿URL、ログURL、未確認事項を示す。
モデルが起動する前の失敗、最初のログ保存前の停止、GitHub自体に接続できない場合はGitHubログが残らない。プラットフォーム実行記録と併せて「起動またはログ保存以前の障害・詳細不明」と扱い、未起動や本文未生成と断定しない。
この仕様の登録・手動ログ試験と、定期実行での成功は別に記録する。
