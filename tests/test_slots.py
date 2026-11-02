import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('media', Path(__file__).parents[1] / 'scripts/english_media.py')
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)

class SlotTests(unittest.TestCase):
    def test_three_articles_and_legacy(self):
        legacy = dict(date='2026-11-02', title='Old', en='Hello', is_preview=False)
        articles = [legacy] + [dict(legacy, title=f'[{slot}] Story') for slot in ['07:00', '12:00', '17:00']]
        for slot in ['07:00', '12:00', '17:00']:
            self.assertEqual(media.article_slot(media.select_article(articles, '2026-11-02', slot)), slot)
        with self.assertRaises(ValueError):
            media.select_article(articles)
        self.assertIn('3級', media.article_level(articles[1]))
        self.assertEqual(media.article_slot(legacy), '')

if __name__ == '__main__':
    unittest.main()
