"""Conservative repetition cleanup, without guessing visual attributes."""
import re

POSITIVE_FILLER = {
    'ultra detailed', 'intricate detailing', 'detailed craftsmanship',
    'anime character details', 'anime character composition', 'anime outfit details',
    'anime eye details', 'anime pose details', 'anime character outfit',
    'anime character accessories', 'anime character hair', 'anime character eyes',
    'anime character pose', 'anime hair style', 'anime character design',
    'anime outfit', 'anime accessories', 'anime hair', 'anime eyes', 'anime pose',
    'anime design',
}
NEGATIVE_FILLER = {
    'extra clothing', 'extra accessory', 'extra accessories', 'extra hair',
    'extra background', 'extra object', 'extra element', 'extra detail', 'extra feature',
    'low effort', 'amature', 'amateur', 'messy',
}
TECHNICAL = {
    'texture', 'material', 'reflection', 'shadow', 'highlight', 'render', 'paint',
    'brushstroke', 'color', 'contrast', 'exposure', 'white balance', 'color grading',
    'tone mapping', 'gamma', 'dynamic range', 'noise reduction', 'sharpening',
    'blur', 'compression', 'artifact', 'distortion', 'aliasing', 'anti aliasing',
    'sampling', 'dithering', 'post processing', 'editing', 'manipulation',
    'enhancement', 'restoration', 'upscaling', 'noise', 'grain',
}
ALIASES = {'wrong anatomy': 'bad anatomy', 'wrong proportions': 'bad proportions',
           'poorly drawn hands': 'deformed hands', 'mutated hands': 'deformed hands',
           'poorly drawn feet': 'deformed feet', 'mutated feet': 'deformed feet',
           'extra limb': 'extra limbs', 'extra finger': 'extra fingers'}


def key(text):
    return re.sub(r'\s+', ' ', text.casefold().replace('-', ' ')).strip(' .,:;')


def clean_phrases(items, negative=False):
    result, seen = [], set()
    for item in items:
        normalized = key(item)
        if negative:
            prefix, _, suffix = normalized.partition(' ')
            if normalized in NEGATIVE_FILLER or (prefix in ('bad', 'extra', 'messy') and suffix in TECHNICAL):
                continue
            normalized = ALIASES.get(normalized, normalized)
        elif normalized in POSITIVE_FILLER:
            continue
        elif normalized in ('anime style', 'anime illustration', 'anime art', 'anime art style'):
            normalized = 'anime illustration'
            item = 'anime illustration'
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(ALIASES.get(key(item), item.strip()) if negative else item.strip())
    return result


def clean_caption(text):
    if text.count(',') >= 6 and text.count('. ') < 3:
        # Some models put a tag list into the sentence field too.
        return ', '.join(clean_phrases(re.split(r'[,\n]+(?![^()]*\))', text)))
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(clean_phrases(sentences))
