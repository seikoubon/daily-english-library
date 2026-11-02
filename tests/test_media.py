import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
import tempfile

spec = importlib.util.spec_from_file_location('media', Path(__file__).parents[1] / 'scripts/english_media.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class MediaTests(TestCase):
    def test_preview_and_duplicates(self):
        a = {'date': '2026-11-02', 'en': 'Hello.', 'is_preview': False}
        self.assertEqual(m.select_article([a, dict(a, date='2026-11-03', is_preview=True)]), a)
        with self.assertRaises(ValueError):
            m.select_article([a, a])

    def test_resume_and_revision(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            a = {'date': '2026-11-02', 'en': 'Hello.'}
            args = SimpleNamespace(voice='male', rate='-10%', burn_subtitles=False)
            async def fake_speech(*_):
                (folder / 'audio.mp3').write_bytes(b'audio')
                (folder / 'subtitles.srt').write_text('subtitle')
            def fake_video(*_, **__):
                (folder / 'output.tmp.mp4').write_bytes(b'video')
            state = {}
            with patch.object(m, 'speech', side_effect=fake_speech) as speech, patch.object(m.subprocess, 'run', side_effect=fake_video) as video:
                m.render(a, folder, state, args)
                m.render(a, folder, state, args)
                self.assertEqual(speech.call_count, 1)
                self.assertEqual(video.call_count, 1)
                with self.assertRaises(RuntimeError):
                    m.render(dict(a, en='Changed.'), folder, state, args)

    def test_uncertain_upload_never_inserts(self):
        import sys
        from unittest.mock import MagicMock
        modules = {'googleapiclient': MagicMock(), 'googleapiclient.discovery': MagicMock(), 'googleapiclient.http': MagicMock()}
        with patch.dict(sys.modules, modules), patch.object(m, 'credentials', return_value=object()):
            with self.assertRaisesRegex(RuntimeError, '前回の投稿結果'):
                m.upload({}, Path('.'), {'upload_started': True}, SimpleNamespace(secrets_dir=Path('.')))
            modules['googleapiclient.discovery'].build.return_value.videos.assert_not_called()

if __name__ == '__main__':
    main()
