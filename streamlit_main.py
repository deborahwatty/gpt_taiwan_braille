import streamlit as st
from cc_main import *


def main():
    st.title("Convert Chinese to Zhuyin and Braille using GPT-4")
    st.write("Please use Traditional characters only, without foreign words.")
    sentence = st.text_input("Enter your sentence: ")
    rerun_button = st.button("Rerun")
    if sentence and rerun_button:
        if only_chinese(sentence):
            try:
                prompt, response = get_formatted_zhuyin_and_braille(sentence)
                zhuyin = response['zhuyin']
                braille = response['braille']
                st.write("Prompt:")
                st.write(f"```\n{prompt}\n```")
                st.write("Zhuyin")
                st.write(f"```\n{zhuyin}\n```")
                st.write("Braille")
                st.write(f"```\n{braille}\n```")
            except ValueError:
                st.write("Please enter only traditional Chinese characters ")


if __name__ == '__main__':
    main()
