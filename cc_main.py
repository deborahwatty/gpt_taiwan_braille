import openai
import os
from prompt_generation import PromptGenerator
from braille_converter import convert_zhuyin_to_braille

openai.api_key = os.environ['OPENAI_API_KEY']


def get_formatted_zhuyin_and_braille(sentence):
    assert only_chinese(sentence)
    prompt_generator = PromptGenerator(sentence)
    _input = prompt_generator.get_formatted_prompt()

    messages = [{"role": "user", "content": _input.to_string()}]
    output = openai.ChatCompletion.create(
        model="gpt-4",
        max_tokens=1500,
        temperature=0,
        messages=messages)

    response_string = output['choices'][0]['message']['content']
    answer_parsed = prompt_generator.get_output_parser().parse(response_string)
    answer_parsed['braille'] = convert_zhuyin_to_braille(answer_parsed['zhuyin'])
    return _input.text, answer_parsed


def only_chinese(sentence):
    punct = ['，', '、', '；', '：', '．', '……', '──', '。', '？', '！', '「', '」', '『', '』', '（', '）', '──', '《', '》', '〈', '〉',
             '※', '◎', '（', '）', '［', '］', '｛', '｝', '—', '～']
    for char in sentence:
        if char not in punct and not ('\u4e00' <= char <= '\u9fff'):
            return False
    return True
