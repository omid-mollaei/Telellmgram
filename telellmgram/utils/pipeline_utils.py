"""Codes required by some pipelines."""

import os 
import pickle
import pandas as pd
from os.path import dirname, abspath
from tqdm import tqdm
from dataclasses import dataclass

dir_root = dirname(dirname(abspath(__file__)))
metadata_file = os.path.join(dir_root, "media", "metadata.csv")
metadata = pd.read_csv(metadata_file)

telegram_group_files = []
for i in range(len(metadata)):
    messges_file = metadata.iloc[i]['messages']
    media_idx    = metadata.iloc[i]['id']
    if 'g' in messges_file.split("/")[-1]:
        telegram_group_files.append((int(media_idx), messges_file))


def get_media_table_from_code(code):
    messages_file = metadata[metadata['id']==code]['messages'].values[0]
    return pd.read_csv(messages_file)


def extract_users_from_groups():
    groups_memebers = {}
    for media_idx, message_file in tqdm(telegram_group_files):
        groups_memebers[media_idx] = {}
        table = get_media_table_from_code(media_idx)
        for i in range(len(table)):
            row = table.iloc[i]
            user_id, user_name = row['sender_name'], row['sender_id']
            if user_id not in groups_memebers[media_idx]:
                groups_memebers[media_idx][user_id] = user_name
    
    with open(os.path.join(dir_root, "media", 'users.pkl'), 'wb') as p:
        pickle.dump(groups_memebers, p)


def get_basic_stat_info():
    NUM_MEDIA_IN_DATABASE = len(metadata)
    NUM_GROUPS = len(metadata[metadata['type'] == 'group'])
    NUM_CHANNELS = NUM_MEDIA_IN_DATABASE - NUM_GROUPS
    