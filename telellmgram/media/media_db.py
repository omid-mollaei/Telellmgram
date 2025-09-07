""" Codes to represents the Telellmgram database in our project """

from dataclasses import dataclass
from dataclasses import field
from os.path import dirname
from enum import Enum
import pandas as pd
import os

dir_root = dirname(dirname(__file__))
metadata_file = os.path.join(dir_root, "media", "metadata.csv")

class MediaType(Enum):
    channel = "channel"
    group = "group"


@dataclass
class MediaMetadata:
    """Main class for holding each of media metadata. Most of the filed are same as features saved for csv metadata file"""
    idx: str = field(
        metadata={"help": "Id of the media"}
    )
    name: str = field(
        metadata={"help": "Name of group or channel."}
    )
    type: MediaType = field(
        metadata={"help": "Whether this media is a channel or a group."}
    )
    messages_file: str = field(
        metadata={"help": "Path to csv file, containing the messages published in the media."}
    )


class TelegramMedia:
    """Main class for representing all the data we have gathered from Telegram. This would be used for :
        1. Hints for selecting various pipelines in various stages
        2: Source of retrival in pipelines.
    """
    def __init__(self):
        self.the_media_metadata_table = pd.read_csv(metadata_file)
        self.the_media = self._build_all_media_database()

    def _build_all_media_database(self):
        the_media = list()
        for i in range(len(self.the_media_metadata_table)):
            media = self.the_media_metadata_table.iloc[i]
            media_md = MediaMetadata(
                idx = media['id'],
                name = media["name"],
                type = media["type"],  # We are sure that its channel or group.
                messages_file =media["messages"]
            )
            the_media.append(media_md)
        return the_media

    def describe(self, add_key=False, write_to_file=None):
        the_media_descriptor_str = ""
        for i, media in enumerate(self.the_media):
            media_descriptor = (f"{i})\n\tMedia idx = {media.idx}\n\tMedia name = {media.name}\n\tMedia type = {media.type}\n\t"
                                "Media message file = {media.messages}")
            if add_key:
                media_descriptor = media_descriptor + f"\n\tKey = {media.key}"
            the_media_descriptor_str += media_descriptor + "\n\n"

        if write_to_file:
            with open(write_to_file, 'w') as f:
                f.write(the_media_descriptor_str)
        return the_media_descriptor_str
