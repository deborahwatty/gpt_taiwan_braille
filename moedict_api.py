import spacy
import requests

# Load the Chinese model
nlp = spacy.load("zh_core_web_sm")


def get_all_pronunciations(input_string):
    # Initialize a dictionary to store combinations and their possible pronunciations
    all_pronunciations = {}

    # Loop over all possible substring lengths
    for i in range(1, len(input_string) + 1):
        # Generate all possible contiguous substrings of length i
        for j in range(len(input_string) - i + 1):
            combination = input_string[j:j+i]
            # Look up the pronunciation of the combination
            url = f"https://www.moedict.tw/uni/{combination}"
            response = requests.get(url)
            data = response.json()
            # Handle variant characters
            if 'heteronyms' in data.keys() and 'definitions' in data['heteronyms'][0].keys() and data['heteronyms'][0]['definitions'][0]['def'].endswith('的異體字。'):
                variant = data['heteronyms'][0]['definitions'][0]['def'][1]
                url = f"https://www.moedict.tw/uni/{variant}"
                response = requests.get(url)
                data = response.json()

            pronunciations = get_pronunciations_for_word(data)
            if pronunciations:
                # Add the combination and its pronunciations to the dictionary
                all_pronunciations[combination] = pronunciations

                # If the combination has more than one character and has a unique pronunciation,
                # add the pronunciation of the combination as a separate entry in the dictionary
                if len(combination) > 1 and len(pronunciations) == 1 and len(pronunciations[0]) == 1:
                    combination_pronunciation = [[pronunciations[0][0].replace(' ', '')]]
                    all_pronunciations[combination] = combination_pronunciation

    return all_pronunciations


def get_pronunciations_for_word(data):
    bopomofo_variants = []

    # Extract the bopomofo variants from each pronunciation
    if 'heteronyms' in data.keys():
        for pronunciation in data["heteronyms"]:
            bopomofo = pronunciation.get("bopomofo")
            if bopomofo and not bopomofo.startswith('（讀音）') and not bopomofo.startswith('（又音）'):
                bopomofo_variants.append(bopomofo.strip('（語音）'))

    return bopomofo_variants


# Define a function to tag a Chinese sentence using SpaCy
def tag_chinese_sentence(sentence):
    doc = nlp(sentence)
    tokens = list()
    pos = list()
    for token in doc:
        tokens.append(token.text)
        pos.append(token.pos_)
    return list(zip(tokens, pos))


def get_moe_tag(spacy_tag):
    pos_to_dict = {
        "NOUN": ["名"],
        "PROPN": ["名"],
        "VERB": ["動", "副"],
        "ADJ": ["形"],
        "ADV": ["副"],
        "DET": ["名", "形"], # for whatever reason, 量詞 are 名 in 萌典 and e.g. 那 is a 形
        "PRON": ["代"],
        "ADP": ["介"],
        "CONJ": ["連"],
        "CCONJ": ["連"],
        "PART": ["助"],
        "NUM": ["數", "名", "形"],
        "PUNCT": ["符"],
        "X": ["動"],
        "INTJ": ["嘆"]
    }
    return pos_to_dict[spacy_tag]


def get_bopomofo_types(data):
    bopomofo_types = []
    for entry in data['heteronyms']:
        for definition in entry['definitions']:
            if 'type' in definition and (entry['bopomofo'], definition['type']) not in bopomofo_types:
                bopomofo_types.append((entry['bopomofo'], definition['type']))
    return bopomofo_types


def find_pronunciation_for_sentence(sentence):
    pronunciations = list()
    for token, pos in tag_chinese_sentence(sentence):
        if pos == 'PUNCT':
            pronunciations.append([token])
        else:
            url = f"https://www.moedict.tw/uni/{token}"
            response = requests.get(url)
            data = response.json()
            token_pron = get_pronunciations_for_word(data)
            if len(token_pron) > 1:
                moe_tags = get_moe_tag(pos)
                pron_tags = get_bopomofo_types(data)
                filtered_tags = [tag for tag in pron_tags if tag[1] in moe_tags]
                pronunciations.append([pron for pron, tag in filtered_tags])
                # pronunciations.append([filtered_tags[0][0]])
            else:
                pronunciations.append(token_pron)
    return pronunciations


def get_all_segmentations(s):
    if len(s) == 0:
        return [[]]
    if len(s) == 1:
        return [[s]]
    result = []
    for i in range(1, len(s)+1):
        prefix = s[:i]
        suffixes = get_all_segmentations(s[i:])
        for suffix in suffixes:
            result.append([prefix] + suffix)
    return sorted(result, key=lambda x: len(x))


def get_valid_segmentations(sentence, pronunciation_dict):
    valid_segmentations = []
    segmentations = get_all_segmentations(sentence)
    for segmentation in segmentations:
        if len(valid_segmentations) == 0 or len(segmentation) <= len(valid_segmentations[0][0]):
            pronunciation = list()
            for token in segmentation:
                if token in pronunciation_dict.keys():
                    pronunciation.append(pronunciation_dict[token])
                else:
                    break
            if len(pronunciation) == len(segmentation):
                valid_segmentations.append((segmentation, pronunciation))
    return valid_segmentations


def best_guess_without_llm(sentence):
    return_word_pron = list()

    word_tag_list = tag_chinese_sentence(sentence)
    pron_list = find_pronunciation_for_sentence(sentence)
    word_pron_list = [(word_tag[0], pron) for word_tag, pron in zip(word_tag_list, pron_list)]

    for word, pron in word_pron_list:
        if len(pron) == 0:
            segmented = sorted(get_valid_segmentations(word, get_all_pronunciations(word)), key=lambda x: len(x[1]))[0]
            for word_part, word_part_pron in zip(segmented[0], segmented[1]):
                return_word_pron.append((word_part, word_part_pron))
        else:
            return_word_pron.append((word, pron))
    return return_word_pron


def replace_chinese_tag(tag):
    tag_words = {
        "名": "Noun",
        "動": "Verb",
        "形": "Adjective",
        "副": "Adverb",
        "代": "Pronoun",
        "介": "Adposition",
        "連": "Conjunction",
        "助": "Particle",
        "數": "Number",
        "符": "Punctuation",
        "嘆": "Exclamation"
    }
    return tag_words.get(tag, tag)


def get_def_examples(character):
    url = f"https://www.moedict.tw/uni/{character}"
    response = requests.get(url)
    data = response.json()

    result = dict()

    for item in data['heteronyms']:
        pinyin = item['bopomofo']
        definitions = item['definitions']

        if definitions and definitions[0]['def']:  # Check if definitions list is not empty and first definition is not empty string
            result[pinyin] = {}

            for i, definition in enumerate(definitions):
                if 'def' in definition.keys() and 'type' in definition.keys() and definition['def'].find('&nbsp')<0:
                    key = i + 1  # Numeric key
                    example_str = definition.get('example', [''])[0]  # Get the first example string (or empty string if not available)
                    example_str = example_str.rstrip('。').split('：', 1)[-1]  # Extract substring starting from the first occurrence of "："
                    examples = [e.strip('「」') for e in example_str.split('、') if e.strip('「」')]  # Split example string, remove surrounding quotes, and exclude empty examples
                    result[pinyin][key] = {
                        'def': definition['def'],
                        'examples': examples,
                        'type': replace_chinese_tag(definition['type'])
                    }
                elif 'def' in definition.keys() and definition['def'].find('&nbsp')<0:
                    key = i + 1  # Numeric key
                    example_str = definition.get('example', [''])[
                        0]  # Get the first example string (or empty string if not available)
                    example_str = example_str.rstrip('。').split('：', 1)[
                        -1]  # Extract substring starting from the first occurrence of "："
                    examples = [e.strip('「」') for e in example_str.split('、') if e.strip(
                        '「」')]  # Split example string, remove surrounding quotes, and exclude empty examples
                    result[pinyin][key] = {
                        'def': definition['def'],
                        'examples': examples,
                        'type': 'word of unknown type'
                    }
    return result


def get_def_examples_pinyin(character):
    url = f"https://www.moedict.tw/uni/{character}"
    response = requests.get(url)
    data = response.json()

    result = dict()

    if 'heteronyms' not in data.keys():
        return None

    for item in data['heteronyms']:
        pinyin = item['pinyin']
        definitions = item['definitions']

        if definitions and definitions[0]['def']:  # Check if definitions list is not empty and first definition is not empty string
            result[pinyin] = {}

            for i, definition in enumerate(definitions):
                if 'def' in definition.keys() and 'type' in definition.keys():
                    key = i + 1  # Numeric key
                    example_str = definition.get('example', [''])[0]  # Get the first example string (or empty string if not available)
                    example_str = example_str.rstrip('。').split('：', 1)[-1]  # Extract substring starting from the first occurrence of "："
                    examples = [e.strip('「」') for e in example_str.split('、') if e.strip('「」')]  # Split example string, remove surrounding quotes, and exclude empty examples
                    result[pinyin][key] = {
                        'def': definition['def'],
                        'examples': examples,
                        'type': replace_chinese_tag(definition['type'])
                    }

    return result
