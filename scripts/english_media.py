"""Daily English: render locally, then optionally upload. Python 3.12+."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request

SOURCE = 'https://raw.githubusercontent.com/seikoubon/daily-english-library/main/daily_english_articles.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']


def save(path, data):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


def select_article(data, date=None):
    if isinstance(data, dict):
        data = data.get('articles', [data])
    candidates = [a for a in data if a.get('is_preview') is False and (not date or a['date'] == date)]
    if not candidates:
        raise ValueError('正式記事がありません。日付・is_previewを確認してください。')
    latest = max(a['date'] for a in candidates)
    matches = [a for a in candidates if a['date'] == latest]
    if len(matches) != 1:
        raise ValueError('同日の正式記事が複数あるため停止しました。')
    a = matches[0]
    if not isinstance(a.get('en'), str) or not a['en'].strip():
        raise ValueError('英文が空です。')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', a['date']):
        raise ValueError('日付形式が不正です。')
    return a


def credentials(root, interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    root.mkdir(parents=True, exist_ok=True)
    token = root / 'token.json'
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if creds and not creds.has_scopes(SCOPES):
        creds = None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            if not interactive:
                raise RuntimeError('認証期限切れです。authコマンドで再認証してください。') from None
            creds = None
    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError('先にauthコマンドを実行してください。')
        creds = InstalledAppFlow.from_client_secrets_file(str(root / 'client_secrets.json'), SCOPES).run_local_server(port=0)
    token.write_text(creds.to_json(), encoding='utf-8')
    try:
        token.chmod(0o600)
    except OSError:
        pass
    return creds


async def speech(text, voice, rate, folder):
    import edge_tts
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, voice, rate=rate).save(str(folder / 'audio.tmp.mp3'), str(folder / 'subtitles.tmp.srt'))
            os.replace(folder / 'audio.tmp.mp3', folder / 'audio.mp3')
            os.replace(folder / 'subtitles.tmp.srt', folder / 'subtitles.srt')
            return
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)


def render(a, folder, state, args):
    fingerprint = hashlib.sha256(json.dumps([a['en'], args.voice, args.rate, args.burn_subtitles, 1], ensure_ascii=False).encode()).hexdigest()
    if state.get('fingerprint') and state['fingerprint'] != fingerprint:
        raise RuntimeError('原稿または制作設定が変更されています。別の--outputを指定してください。')
    state['fingerprint'] = fingerprint
    state['article_date'] = a['date']
    save(folder / 'state.json', state)
    (folder / 'input.txt').write_text(a['en'], encoding='utf-8')
    if not (state.get('audio_done') and (folder / 'audio.mp3').exists() and (folder / 'subtitles.srt').exists()):
        asyncio.run(speech(a['en'], args.voice, args.rate, folder))
        state['audio_done'] = True
        save(folder / 'state.json', state)
    if not (state.get('video_done') and (folder / 'output.mp4').exists()):
        if not shutil.which('ffmpeg'):
            raise RuntimeError('FFmpegをインストールしてください。')
        cmd = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=0x14243b:s=1920x1080:r=25', '-i', 'audio.mp3']
        # Fixed relative filename avoids Windows drive-letter/filter escaping problems.
        if args.burn_subtitles:
            cmd += ['-vf', "subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=24,Outline=2,Alignment=2,MarginV=40'"]
        cmd += ['-c:v', 'libx264', '-preset', 'fast', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '160k', '-pix_fmt', 'yuv420p', '-shortest', '-movflags', '+faststart', 'output.tmp.mp4']
        subprocess.run(cmd, cwd=folder, check=True)
        os.replace(folder / 'output.tmp.mp4', folder / 'output.mp4')
        state['video_done'] = True
        save(folder / 'state.json', state)


def retry_chunk(request):
    from googleapiclient.errors import HttpError
    for attempt in range(5):
        try:
            return request.next_chunk(num_retries=0)
        except HttpError as e:
            if e.resp.status not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
        except (OSError, TimeoutError):
            if attempt == 4:
                raise
        time.sleep(min(2 ** attempt, 16))


def upload(a, folder, state, args):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    youtube = build('youtube', 'v3', credentials=credentials(args.secrets_dir))
    if not state.get('video_id'):
        if state.get('upload_started'):
            raise RuntimeError('前回の投稿結果が不明です。YouTube Studioで確認後、--adopt-video-id IDで登録してください。自動再投稿しません。')
        body = {'snippet': {'title': (f"Daily English B1 | {a['date']} | {a['title']}")[:100], 'description': f"{a['title']}\n{a.get('ja_title', '')}\n\n英検2級・CEFR B1目安。合成音声を使用。\n英文・日本語訳・重要表現:\nhttps://seikoubon.github.io/daily-english-library/\n記事日付: {a['date']}", 'categoryId': '27'}, 'status': {'privacyStatus': args.privacy, 'selfDeclaredMadeForKids': False}}
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(str(folder / 'output.mp4'), mimetype='video/mp4', chunksize=8 * 1024 * 1024, resumable=True))
        state['upload_started'] = True
        save(folder / 'state.json', state)
        result = None
        while result is None:
            _, result = retry_chunk(request)
        state['video_id'] = result['id']
        save(folder / 'state.json', state)
    if not args.burn_subtitles and not state.get('caption_id'):
        # Listing first recovers a caption upload whose response was lost.
        tracks = youtube.captions().list(part='snippet', videoId=state['video_id']).execute()
        existing = [t for t in tracks.get('items', []) if t['snippet'].get('name') == 'Daily English EN']
        if existing:
            state['caption_id'] = existing[0]['id']
        else:
            result = youtube.captions().insert(part='snippet', body={'snippet': {'videoId': state['video_id'], 'language': 'en', 'name': 'Daily English EN', 'isDraft': False}}, media_body=MediaFileUpload(str(folder / 'subtitles.srt'), mimetype='application/octet-stream')).execute()
            state['caption_id'] = result['id']
        save(folder / 'state.json', state)
    print('https://youtu.be/' + state['video_id'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['render', 'publish', 'auth'])
    p.add_argument('--source', default=SOURCE)
    p.add_argument('--date')
    p.add_argument('--output', type=Path, default=Path('media'))
    p.add_argument('--secrets-dir', type=Path, default=Path('secrets'))
    p.add_argument('--voice', default='en-US-ChristopherNeural')
    p.add_argument('--rate', default='-10%')
    p.add_argument('--burn-subtitles', action='store_true')
    p.add_argument('--privacy', choices=['private', 'unlisted', 'public'], default='private')
    p.add_argument('--adopt-video-id')
    args = p.parse_args()
    args.secrets_dir = args.secrets_dir.resolve()
    if args.command == 'auth':
        credentials(args.secrets_dir, True)
        print('認証を保存しました。')
        return
    if args.source.startswith('https://'):
        with urllib.request.urlopen(args.source, timeout=30) as r:
            data = json.load(r)
    else:
        data = json.loads(Path(args.source).read_text(encoding='utf-8-sig'))
    a = select_article(data, args.date)
    folder = (args.output / a['date']).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / '.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError('同時実行中、または前回が強制終了しました。実行中でないことを確認して.lockを削除してください。') from None
    os.close(fd)
    try:
        path = folder / 'state.json'
        state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        render(a, folder, state, args)
        if args.adopt_video_id:
            if not re.fullmatch(r'[A-Za-z0-9_-]{11}', args.adopt_video_id):
                raise ValueError('動画ID形式が不正です。')
            if state.get('video_id') and state['video_id'] != args.adopt_video_id:
                raise ValueError('登録済み動画IDと異なります。')
            state['video_id'] = args.adopt_video_id
            save(path, state)
        if args.command == 'publish':
            upload(a, folder, state, args)
        print('保存先:', folder)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'エラー: {e}', file=sys.stderr)
        sys.exit(1)
