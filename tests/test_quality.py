import unittest
from snuwcaption.quality import clean_phrases, clean_caption
from snuwcaption.output import normalize_output


class QualityTests(unittest.TestCase):
    def test_duplicate_category_padding_removed_without_losing_clothing(self):
        rows = ['white shorts', 'anime character hair', 'Anime Style', 'anime art',
                'white shorts', 'dark blue coat tails', 'white hair', 'blue highlights']
        self.assertEqual(clean_phrases(rows), ['white shorts', 'anime illustration',
                         'dark blue coat tails', 'white hair', 'blue highlights'])

    def test_negative_padding_removed_but_precise_failures_preserved(self):
        rows = ['extra fingers', 'extra finger', 'extra clothing', 'extra accessory',
                'bad gamma', 'extra tone mapping', 'bad anatomy', 'wrong anatomy',
                'blurry', 'mutated hands', 'poorly drawn hands']
        self.assertEqual(clean_phrases(rows, negative=True),
                         ['extra fingers', 'bad anatomy', 'blurry', 'deformed hands'])

    def test_comma_lists_inside_json_array_are_deduplicated(self):
        result = normalize_output('{"caption":"A figure.","tags":["solo, white shorts, solo"],"negative_tags":[]}')
        self.assertEqual(clean_phrases(result['tags']), ['solo', 'white shorts'])

    def test_sentence_repetition_removed_and_region_colors_kept(self):
        self.assertEqual(clean_caption('White shorts. White shorts. Blue coat tails.'),
                         'White shorts. Blue coat tails.')
        self.assertEqual(clean_phrases(['white glove', 'black glove', 'thick outlines', 'flat colors']),
                         ['white glove', 'black glove', 'thick outlines', 'flat colors'])
