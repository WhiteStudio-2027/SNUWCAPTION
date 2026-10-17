"""Bounded recovery of common model formatting variations; never execute output."""
import json
import re


class OutputError(ValueError):
    pass


def normalize_output(content):
    if not isinstance(content, str) or not content.strip():
        raise OutputError('empty_output')
    if len(content) > 100_000:
        raise OutputError('output_too_large')
    text = content.strip()
    if text.startswith('<think>') and '</think>' in text:
        text = text.split('</think>', 1)[1].strip()
    blocks = re.findall(r'```[^\n]*\n(.*?)```', text, re.S)
    candidate = blocks[0].strip() if len(blocks) == 1 else text
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        # The reference system prompt uses two code blocks for chat output.
        if len(blocks) == 2 and not blocks[0].lstrip().startswith('{'):
            value = {'positive_prompt': blocks[0].strip(), 'negative_prompt': blocks[1].strip()}
        else:
            # Accept a single JSON object surrounded by prose, but not truncated JSON.
            begin = candidate.find('{')
            if begin < 0:
                raise OutputError('invalid_json') from None
            try:
                value, end = json.JSONDecoder().raw_decode(candidate, begin)
            except json.JSONDecodeError:
                raise OutputError('invalid_json') from None
            if candidate[end:].strip() and '{' in candidate[end:]:
                raise OutputError('multiple_outputs')
    if not isinstance(value, dict):
        raise OutputError('expected_object')

    def phrases(item):
        if item is None:
            return []
        if isinstance(item, str):
            return [part.strip() for part in re.split(r'[,\n]+', item) if part.strip()]
        if not isinstance(item, list) or any(not isinstance(t, str) for t in item):
            raise OutputError('invalid_tag_type')
        return [phrase.strip() for entry in item for phrase in re.split(r'[,\n]+(?![^()]*\))', entry) if phrase.strip()]

    positive = value.get('positive_prompt', value.get('positive', ''))
    caption = value.get('caption') or positive
    tags = phrases(value.get('tags', positive or caption))
    if not tags and isinstance(caption, str) and caption.strip():
        tags = phrases(caption)
    if not caption and tags:
        caption = ', '.join(tags)
    negatives = phrases(value.get('negative_tags', value.get('negative_prompt', value.get('negative', []))))
    uncertainty = phrases(value.get('uncertainties', []))
    if not isinstance(caption, str) or not caption.strip() or not tags:
        raise OutputError('missing_positive')
    # Extra explanatory keys are discarded, never interpreted as instructions.
    return {'caption': caption, 'tags': tags, 'negative_tags': negatives, 'uncertainties': uncertainty}
