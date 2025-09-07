"""Textual preprocessing functions."""

import re
import hashlib

persian_alphabets_normalized = {
    'ي': 'ی',  # Arabic ي to Persian ی
    'ك': 'ک',  # Arabic ك to Persian ک
    'ة': 'ه',  # Arabic ة to Persian ه
    'ۀ': 'ه',
    'ى': 'ی',  # Arabic ى to Persian ی
    'ؤ': 'و',  # Arabic ؤ to Persian و (in some contexts)
    'إ': 'ا',  # Arabic إ to Persian ا (not always, but commonly replaced)
    'أ': 'ا',  # Arabic أ to Persian ا (not always, but commonly replaced)
    'ء': '',  # Arabic ء (hamze) often removed in Persian text normalization
    '?': '؟',
}

def add_whitespace_around_holly_abbrev(input_string):
    pattern = r'\([^\n]{1,2}\)'
    result = re.sub(pattern, r' \g<0> ', input_string)
    return result

def normalize_persian_sentence(sentence: str):
    for un_normalized_alpha, normalized in persian_alphabets_normalized.items():
        sentence = sentence.replace(un_normalized_alpha, normalized)
    return sentence


def remove_extra_newlines(input_string):
    cleaned_string = re.sub(r'\n+', '\n', input_string)
    return cleaned_string

def clean_text(input_str):
    pattern = re.compile(r'[^\u0600-\u06FF\uFB8A\u067E\u0686\u06AF\u06F0-\u06F9a-zA-Z0-9] :?.,!؟،*-_\(\)\[] ')
    cleaned_str = pattern.sub('', input_str)
    return cleaned_str


def add_whitespace_around_numbers(sentence):
    def add_whitespace(match):
        return f' {match.group(0)} '
    english_number_pattern = r'(\d+\.\d+|\d+)'
    persian_number_pattern = r'(?<!\S)([۰-۹]+(٫[۰-۹]+)?)'
    combined_pattern = f'({english_number_pattern}|{persian_number_pattern})'
    modified_text = re.sub(combined_pattern, add_whitespace, sentence)
    return modified_text.strip()


def preprocess_persian_sentence(sentence):
    sentence = normalize_persian_sentence(sentence)
    sentence = add_whitespace_around_holly_abbrev(sentence)
    ready_sentences = add_whitespace_around_numbers(sentence)
    return ready_sentences


def find_first_digit(input_string):
    for char in input_string:
        if char.isdigit():
            return char
    return None  # Return None if no digit is found


def remove_empty_lines(input_string):
    lines = input_string.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    output_string = "\n".join(non_empty_lines)
    return output_string


def get_current_date():
    #current_date = datetime.now()
    #formatted_date = current_date.strftime("%d/%m/%Y")
    #return formatted_date
    return '04/09/205'


def generate_unique_key(input_string):
    hash_object = hashlib.sha256(input_string.encode())
    hash_hex = hash_object.hexdigest()
    unique_key = hash_hex[:7]
    return unique_key


def count_persian_letters(text):
    # Persian alphabet letters
    persian_letters = "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"
    
    count = 0
    for char in text:
        if char in persian_letters:
            count += 1
    return count

