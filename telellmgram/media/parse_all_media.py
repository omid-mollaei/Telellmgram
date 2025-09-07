"""This scripts parse all the exported data from telegram to pandas dataframe and add their metadata"""

import os, re
import json
import pandas as pd
from tqdm import tqdm
from typing import Union
from os.path import dirname
from datetime import datetime
from telellmgram.utils.text_utils import preprocess_persian_sentence
from telellmgram.utils.text_utils import remove_extra_newlines, clean_text


# ====== Initialization =========== #
dir_root = dirname(dirname(__file__))
dir_raw_data = os.path.join(dir_root, 'media', 'media_raw')
dir_parsed_data = os.path.join(dir_root, 'media', 'media_parsed')

folders_raw = os.listdir(dir_raw_data)
folders_raw = [os.path.join(dir_raw_data, f) for f in folders_raw if not '.' in f]  # skip names with extension (files)
print(f"Found {len(folders_raw)} in raw data folder.")


# ======= Define required functions ======== #
def detect_chat_type(json_data: Union[str, dict]):
    """
    Detects whether the exported Telegram data is from a channel or a group.
    json_data: The parsed JSON data from the Telegram export
    """
    if isinstance(json_data, str) and json_data.endswith('.json'):
        with open(json_data, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    if 'channel' in json_data['type']:
        return 'channel'
    elif 'group' in json_data['type']:
        return 'group'
    return 'unknown'


def preprocess_text_for_export(raw_text, links, hashtags):
    text = preprocess_persian_sentence(raw_text)
    for token in links + hashtags:
        text = text.replace(token, "")
    text = remove_extra_newlines(clean_text(text))
    return text


def preprocess_text(raw_text, links, hashtags):
    text = preprocess_persian_sentence(raw_text)
    for token in links + hashtags:
        text = text.replace(token, "")
    text = remove_extra_newlines(clean_text(text))
    return text


def extract_links(input_string):
    url_pattern = re.compile(
        r'(?:(?:https?://|www\.)\S+|(?:t\.me/\S+)|(?:\S+\.com)|(?:\S+\.org)|(?:\S+\.net)|(?:\S+\.io)|(?:\S+\.co)|(?:@\w+))'
    )
    links = url_pattern.findall(input_string)
    return links


def extract_hashtags(input_string):
    hashtag_pattern = re.compile(r'#\w+')
    hashtags = hashtag_pattern.findall(input_string)
    return hashtags


def parse_reactions(reactions):
    """Format reactions as emoji:count pairs"""
    if not reactions:
        return ""
    return ",".join([f"{r['emoji']}:{r['count']}" for r in reactions if r['type'] == "emoji"])


def telegram_json_channel_to_dataframe(data):
    """
    Convert Telegram channel JSON export to a structured pandas DataFrame.
    Args:
        data: JSON data loaded from Telegram export file
    Returns:
        pandas.DataFrame with columns:
        - message_id
        - raw_text
        - cleaned_text
        - time (hh:mm:ss)
        - date (dd/mm/yy)
        - reactions (emoji:count pairs)
        - links (comma-separated)
        - hashtags (comma-separated)
    """
    messages = []
    print(f"Processing media: {data['name']}")
    for msg in tqdm(data['messages']):
        if msg['type'] != 'message':
            continue
        if isinstance(msg['text'], list):
            raw_text = ''.join([item['text'] if isinstance(item, dict) else item for item in msg['text']])
        else:
            raw_text = msg['text']
        if raw_text.endswith("\n"):
            raw_text = raw_text[:-2]
        dt = datetime.strptime(msg['date'], "%Y-%m-%dT%H:%M:%S")
        links = extract_links(raw_text)
        hashtags = extract_hashtags(raw_text)

        message = {
            'message_id': msg['id'],
            'raw_text': raw_text,
            'cleaned_text': remove_extra_newlines(preprocess_text(raw_text, links, hashtags)),
            'time': dt.strftime("%H:%M:%S"),
            'date': dt.strftime("%d/%m/%y"),
            'reactions': parse_reactions(msg.get('reactions', [])),
            'links': ",".join(links),
            'hashtags': ",".join(hashtags)
        }
        messages.append(message)
    return pd.DataFrame(messages)


def telegram_json_group_to_dataframe(data):
    """
    Convert Telegram group JSON export to a structured pandas DataFrame.
    Args:
        data: JSON data loaded from Telegram export file
    Returns:
        pandas.DataFrame with columns:
        - message_id
        - raw_text
        - cleaned_text
        - sender_name
        - sender_id
        - time (hh:mm:ss)
        - date (dd/mm/yy)
        - reactions (emoji:count pairs)
        - links (comma-separated)
        - hashtags (comma-separated)
        - reply_to_message_id
    """
    messages = []
    print(f"Processing group: {data['name']}")

    for msg in tqdm(data['messages']):
        if msg['type'] != 'message':
            continue

        if isinstance(msg['text'], list):
            raw_text = ''.join([item['text'] if isinstance(item, dict) else item for item in msg['text']])
        else:
            raw_text = msg['text']

        dt = datetime.strptime(msg['date'], "%Y-%m-%dT%H:%M:%S")
        links = extract_links(raw_text)
        hashtags = extract_hashtags(raw_text)

        message = {
            'message_id': msg['id'],
            'raw_text': raw_text,
            'cleaned_text': preprocess_text(raw_text, links, hashtags),
            'sender_name': msg.get('from', ''),
            'sender_id': msg.get('from_id', ''),
            'time': dt.strftime("%H:%M:%S"),
            'date': dt.strftime("%d/%m/%y"),
            'reactions': parse_reactions(msg.get('reactions', [])),
            'links': ",".join(links),
            'hashtags': ",".join(hashtags),
            'reply_to_message_id': msg.get('reply_to_message_id', None)
        }
        messages.append(message)
    return pd.DataFrame(messages)


def parse_all_media():
    meta_data = []  # Initialize an empty metadata file 

    for i, media_data in enumerate(folders_raw):
        print(f"{i+1}/{len(folders_raw)}) Parsing: {media_data}")

        if not media_data.endswith('.json'):
            media_data = os.path.join(media_data, 'result.json')
        with open(media_data, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chat_type = detect_chat_type(data)
        if chat_type == 'channel':
            media = telegram_json_channel_to_dataframe(data)
        elif chat_type == 'group':
            media = telegram_json_group_to_dataframe(data)
        else:
            raise ValueError('Unknown chat type. Chat type must be either a channel or a group')

        output_filename = os.path.join(dir_parsed_data, f'{i+1}{chat_type[0]}.csv')
        media.to_csv(output_filename, index=False)
        meta_data.append([
            data['id'],
            data['name'],
            chat_type,
            output_filename,
        ])

    meta_data_df = pd.DataFrame(meta_data, columns=['id', 'name', 'type', 'messages'])
    meta_data_df.to_csv(os.path.join(dir_root, 'media', 'metadata.csv'))


if __name__ == "__main__":
    parse_all_media()