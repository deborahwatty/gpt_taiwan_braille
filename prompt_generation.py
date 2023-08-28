from langchain.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from moedict_api import get_def_examples, best_guess_without_llm

# os.environ['OPENAI_API_KEY'] = 'XYZ'


class PromptGenerator:
    def __init__(self, sentence):
        self.preprocessed = best_guess_without_llm(sentence)
        self.response_schemas = [
            ResponseSchema(name="zhuyin",
                           description="The sentence in Zhuyin only: replace every character by its Zhuyin, keeping "
                                       "the order of the original sentence, e.g. 少了幾件 -> ㄕㄠˇ ˙ㄌㄜ ㄐㄧˇ ㄐㄧㄢˋ")
        ]

        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        self.format_instructions = self.output_parser.get_format_instructions()
        self.template = '''I want to find the Zhuyin for the following sentence:\n{sentence}\nI have already tokenized the sentence and found the following pronunciations:\n{known_zhuyin}\n{dictionary}\nGiven this information, can you convert the sentence to Zhuyin, including the ambiguous ones? {format_instructions}'''

        self.multiple_input_prompt = PromptTemplate(
            template=self.template,
            input_variables=["sentence", "known_zhuyin", "dictionary"],
            partial_variables={"format_instructions": self.format_instructions}
        )

        self.formatted_prompt = self.multiple_input_prompt.format_prompt(sentence=sentence,
                                                                         known_zhuyin=self.generate_all_meaning_strings(),
                                                                         dictionary=self.relevant_dictionary_entries())

    def get_formatted_prompt(self):
        return self.formatted_prompt

    def get_output_parser(self):
        return self.output_parser

    def generate_meaning_string(self, character):
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

        character_dict = get_def_examples(character)
        meaning_string = f"The character {character} can have the following meanings:\n\n"
        list_number = 1
        for pinyin, meanings in character_dict.items():
            for _, meaning in meanings.items():
                if 'def' in meaning.keys() and 'type' in meaning.keys():
                    definition = meaning['def']
                    examples = ', '.join(meaning['examples'])
                    char_type = meaning['type']
                    meaning_string += f"{list_number}. {char_type} meaning \"{definition}\"."
                    if examples:
                        meaning_string += f" For example: {examples}."
                    meaning_string += f" In this case, the Zhuyin is \"{pinyin.lower()}\".\n"
                    list_number += 1
        return meaning_string

    def generate_all_meaning_strings(self):
        known_zhuyin = []
        for word, pron_list in self.preprocessed:
            if len(pron_list) > 1:
                known_zhuyin.append(''.join([word, '-', 'unknown']))
            else:
                known_zhuyin.append(''.join([word, '-', pron_list[0]]))
        return '\n'.join(known_zhuyin)

    def relevant_dictionary_entries(self):
        entries = ['The Zhuyin for the characters marked as unknown is ambiguous.']
        for word, pron_list in self.preprocessed:
            if len(pron_list) > 1:
                entries.append(self.generate_meaning_string(word))
            else:
                pass
        if len(entries) == 1:
            return ''
        return '\n'.join(entries)
