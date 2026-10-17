import unittest
from snuwcaption.output import normalize_output, OutputError


class OutputTests(unittest.TestCase):
    def test_fenced_json_and_comma_tags(self):
        value = normalize_output('```json\n{"caption":"A figure.","tags":"solo, blue jacket","negative_prompt":"duplicate, blur"}\n```')
        self.assertEqual(value['tags'], ['solo', 'blue jacket'])
        self.assertEqual(value['negative_tags'], ['duplicate', 'blur'])
        self.assertEqual(value['uncertainties'], [])

    def test_two_chat_blocks(self):
        value = normalize_output('```\nsolo, short hair, blue jacket\n```\n```\nduplicate, extra limbs\n```')
        self.assertEqual(value['tags'][1], 'short hair')
        self.assertEqual(value['negative_tags'], ['duplicate', 'extra limbs'])

    def test_alias_fields_and_surrounding_prose(self):
        value = normalize_output('Result: {"positive_prompt":"solo, white shorts","negative_prompt":"skirt","notes":"ignored"} End.')
        self.assertEqual(value['caption'], 'solo, white shorts')
        self.assertNotIn('notes', value)

    def test_truncated_json_and_nonstring_tags_rejected(self):
        for text in ('{"caption":"x","tags":["solo"]', '{"caption":"x","tags":[42]}', 'not JSON'):
            with self.subTest(text=text), self.assertRaises(OutputError):
                normalize_output(text)

    def test_no_positive_fabrication(self):
        with self.assertRaises(OutputError):
            normalize_output('{"negative_prompt":"bad hands"}')

    def test_tags_only_remain_observations(self):
        value = normalize_output('{"tags":["solo","blue coat"]}')
        self.assertEqual(value['caption'], 'solo, blue coat')
        self.assertEqual(value['negative_tags'], [])
