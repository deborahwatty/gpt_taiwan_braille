import re
import pandas as pd

df = pd.read_csv("zhuyin2braille.csv")

punct = ['，',
 '、',
 '；',
 '：',
 '．',
 '……',
 '──',
 '。',
 '？',
 '！',
 '「',
 '」',
 '『',
 '』',
 '（',
 '）',
 '──',
 '《',
 '》',
 '〈',
 '〉',
 '※',
 '◎',
 '（',
 '）',
 '［',
 '］',
 '｛',
 '｝',
 '—',
 '～']

zhuyin = ['ㄅ',
 'ㄆ',
 'ㄇ',
 'ㄈ',
 'ㄉ',
 'ㄊ',
 'ㄋ',
 'ㄌ',
 'ㄍ',
 'ㄎ',
 'ㄏ',
 'ㄐ',
 'ㄑ',
 'ㄒ',
 'ㄓ',
 'ㄔ',
 'ㄕ',
 'ㄖ',
 'ㄗ',
 'ㄘ',
 'ㄙ',
 'ㄚ',
 'ㄛ',
 'ㄜ',
 'ㄝ',
 'ㄞ',
 'ㄟ',
 'ㄠ',
 'ㄡ',
 'ㄢ',
 'ㄣ',
 'ㄤ',
 'ㄥ',
 'ㄦ',
 'ㄧ',
 'ㄨ',
 'ㄩ',
 'ˉ',
 'ˊ',
 'ˇ',
 'ˋ',
 '˙']


def find_single_braille_character(df, string, mode="no-check"):
    filtered_df = df[df["zhuyin"] == string]

    if not filtered_df.empty:
        if filtered_df.shape[0] == 1:
            if mode == "i" and filtered_df['type'].iloc[0] != "initial":
                raise ValueError("Non-initial Zhuyin in initial position: " + string)
            if mode == "f" and filtered_df['type'].iloc[0] != "final":
                raise ValueError("Non-final Zhuyin in final position: " + string)
            if mode == "t" and filtered_df['type'].iloc[0] != "tone":
                raise ValueError("Non-tone Zhuyin in tone position: " + string)
            braille_value = filtered_df['braille'].iloc[0]
            return braille_value
        else:
            raise ImplementationError("Need to do disambiguation here")
    else:
        raise ValueError("Illegal Zhuyin: " + string)


def convert_character_to_braille(zhuyin_for_character):
    pattern = r'^([˙˙]?)([\u3105-\u3119]?)([\u311A-\u312A]{0,2})([ˊˇˋ˙]?)'
    matches = re.match(pattern, zhuyin_for_character)

    braille = ""
    if matches and zhuyin_for_character[0] not in punct and zhuyin_for_character[0] not in ['…', '─']:
        neutral_tone = matches.group(1)
        initial = matches.group(2)
        final = matches.group(3)
        tone_mark = matches.group(4)

        if initial:
            braille += find_single_braille_character(df, initial, mode="i")
        if final:
            braille += find_single_braille_character(df, final, mode="f")
        else:
            braille += "⠱"
        if tone_mark:
            braille += find_single_braille_character(df, tone_mark, mode="t")
        if neutral_tone:
            braille += find_single_braille_character(df, neutral_tone, mode="t")
        if not tone_mark and not neutral_tone:
            braille += "⠄"
    else:
        i = 0
        while i < len(zhuyin_for_character):
            if zhuyin_for_character[i] in ['…', '─'] and i + 1 < len(zhuyin_for_character) and zhuyin_for_character[i+1] == zhuyin_for_character[i]:
                braille += find_single_braille_character(df, zhuyin_for_character[i:i+2])
                i += 1
            else:
                braille += find_single_braille_character(df, zhuyin_for_character[i])
            i += 1

    return braille


def identify_character_set(char):
    if char in zhuyin or re.match(r'\s', char):
        return 1
    if char in punct:
        return 2
    return 0


def cut_string(sentence):
    parts = []
    chartype = 0
    if len(sentence) > 0:
        parts.append(sentence[0])
        chartype = identify_character_set(parts[-1][0])
    i = 1
    while i < len(sentence):
        type_next = identify_character_set(sentence[i])
        if chartype == type_next:
            parts[-1] += sentence[i]
        else:
            chartype = type_next
            parts.append(sentence[i])
        i += 1

    return parts


def convert_zhuyin_to_braille(zhuyin_string, return_as_list=False):
    converted = list()

    substrings = cut_string(zhuyin_string)
    strings = []
    for substring in substrings:
        strings.extend(substring.split())
    for string in strings:
        converted.append(convert_character_to_braille(string))

    if return_as_list:
        return converted

    return ''.join(converted).strip('')
