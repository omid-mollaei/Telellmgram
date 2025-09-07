"""Code for working with social and political pipelines"""

import os
import time
import calendar
import numpy as np
import pandas as pd
from tqdm import tqdm
from random import sample
from os.path import dirname, abspath
from telellmgram.media.media_db import metadata_file
from telellmgram.utils.text_utils import count_persian_letters
from telellmgram.utils.llm_utils import call_llm
from telellmgram.utils.pipeline_utils import extract_users_from_groups
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh.filedb.filestore import RamStorage
import matplotlib.pyplot as plt
import seaborn as sns


dir_root = dirname(dirname(__file__))
meta_data = pd.read_csv(metadata_file)
new_line_token = '\n'

def filter_dataframe_by_date(table, start_date, end_date):
    df_copy = table.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'], format="%d/%m/%y", errors="coerce")
    def parse_date(date_str):
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return pd.to_datetime(date_str, format=fmt)
            except (ValueError, TypeError):
                continue
        try:
            day, month, year = map(int, date_str.split("/"))
            last_day = calendar.monthrange(year, month)[1]
            return pd.to_datetime(f"{last_day}/{month}/{year}", dayfirst=True)
        except Exception:
            return pd.NaT
    start_date_parsed = parse_date(start_date)
    end_date_parsed = parse_date(end_date)
    if pd.isna(start_date_parsed):
        raise ValueError(f"Invalid start_date: {start_date}")
    if pd.isna(end_date_parsed):
        raise ValueError(f"Invalid end_date: {end_date}")
    filtered_df = df_copy[(df_copy['date'] >= start_date_parsed) & (df_copy['date'] <= end_date_parsed)]
    filtered_df['date'] = filtered_df['date'].dt.strftime('%d/%m/%y')
    return filtered_df


def get_media_table_from_code(code):
    messages_file = meta_data[meta_data['id']==code]['messages'].values[0]
    return pd.read_csv(messages_file)


def get_media_name_from_code(code):
    return meta_data[meta_data['id']==code]['name'].values[0]


class SpecificMediaAnalysis:
    def __init__(self, prompt, media_idx, start_date=None, end_date=None):
        self.prompt = prompt
        self.messages_file = meta_data[meta_data['id']==media_idx]['messages'].values[0]
        self.media_content = pd.read_csv(self.messages_file)
        self.media_type = meta_data[meta_data['id']==media_idx]['type'].values[0]
        
        if start_date is None:
            start_date = '01/01/00'   # 01/01/2000
        if end_date is None:
            end_date = '01/01/30'
        self.media_content = filter_dataframe_by_date(self.media_content, start_date, end_date)        

        self.prompt_header = f"I want you to perform a telegram analysis based on an input prompt. Below is first the input prompt and then the "\
                             f"messages sent to that media. The media is infact a telegram {self.media_type}. The messages might be a chunk of all messages ."\
                             f"I truncated to prevent a long input."
        self.prompt_channel_format = f"Each row is a message sent to this channel. The format of input in each row is like this:\n"\
                                     f"Message : message_id--message_text--reactions_to_message\n"
        self.prompt_group_format = f"Each row is a message sent to this group. The format of input in each row is like this:\n"\
                                   f"Message : message_id--message_text--reactions_to_message\n"
        self.prompt_footer = f"**Please perform the request analysis in maximum 500 words in one Persian language paragraph**.\n"


    def run(self):
        # Generate chunks
        print("[Runtime Log] -- Request anlysis started on pipeline 1.")
        print("[Runtime Log] -- Generating chunks ...")
        chunks = []
        chunk = self.prompt_header
        chunk = chunk + self.prompt_channel_format if self.media_type == 'channel' else self.prompt_group_format
        chunk = chunk + f"\n\n**User prompt : {self.prompt} **\n\nMessages:\n" 
        for i in tqdm(range(len(self.media_content))):
            row = self.media_content.iloc[i]
            if not isinstance(row['cleaned_text'], str):
                continue
            if count_persian_letters(row['cleaned_text']) < 20:
                continue
            chunk = chunk + self._update_chunk_for_prompt(row) + '\n'
            if len(chunk) >= 200_000:
                chunks.append(chunk + f'\n\n{self.prompt_footer}')
                chunk = self.prompt_header
                chunk = chunk + self.prompt_channel_format if self.media_type == 'channel' else self.prompt_group_format
                chunk = chunk + f"\n\n**User prompt : {self.prompt} **\n\nMessages:\n" 
        print(f"[Runtime Log] -- Number of chunks : {len(chunks)}")

        # Generate Response
        ## Reduce the number of the chunks to decrease llms api calling (just for development)
        develop_mode = True
        selected_chunks = sample(chunks, 5) if len(chunks) > 5 else chunks
        selected_chunks = selected_chunks if develop_mode else chunks
        print(f"[Runtime Log] -- Calling LLM Api. Please wait.")
        responses = []
        with open(os.path.join(dir_root, 'logs', '.pl1_cached.txt'), 'a') as f, open(os.path.join(dir_root, 'logs', '.pl1_responses.txt'), 'w') as g:
            for chunk in tqdm(selected_chunks):
                response = call_llm(chunk)
                time.sleep(25)
                responses.append(response)
                f.write(f"[INPUT]\n{chunk}\n[OUTPUT]\n{response}\n[END]\n")
                g.write(f"{response}\n")
        
        ## Generate final response
        print(f"[Runtime Log] -- Generating Final Response.")
        final_prompt = f"I want to perform an analysis on a telegram {self.media_content}. Below is first the required analysis and then the partial analysis.\n\n"\
        f"** User required analysis : {self.prompt} **\n\n And below are the partial analysis which have benn already performed on various data of this media.\n\n"\
        f"Partial analysis:\n"
        for i, response in enumerate(responses):
            final_prompt += f"{i+1}) {response}\n\n"
        final_prompt = final_prompt + "**Please conclude these partial analysis into a final and complete one and write a paragraph of maximum 800 words in Persian.**"        
        final_output = call_llm(final_prompt)
        with open(os.path.join(dir_root, 'logs', '.pl1_cached.txt'), 'a') as f:
            f.write(f"[INPUT]\n{final_prompt}\n[OUTPUT]\n{final_output}\n[END]\n")

        return final_output
    

    def _update_chunk_for_prompt(self, row_seris):
        if self.media_type == 'channel':
            return f'Message : {row_seris["message_id"]}--{row_seris["cleaned_text"].replace(new_line_token, "")}--{row_seris["reactions"]}'
        else:
            return f'Message : {row_seris["message_id"]}--{row_seris["cleaned_text"].replace(new_line_token, "")}--{row_seris["reactions"]}'


class TopicOriented:
    def __init__(self, prompt, media_codes: list, keywords: list = None, start_date = None, end_date = None):
        self.prompt = prompt
        self.media_codes = media_codes
        self.keywords = keywords
        
        if start_date is None:
            start_date = '01/01/00'   # 01/01/2000
        if end_date is None:
            end_date = '01/01/30'

        self.media_contents = {}
        for code in media_codes:
            self.media_contents[code] = (get_media_name_from_code(code), filter_dataframe_by_date(get_media_table_from_code(code), start_date=start_date, end_date=end_date))


    def run(self):
        # Prepare keywords
        print("[Runtime Log] -- Requested anlysis started on pipeline 2.")
        if self.keywords is None:
            print("[Runtime Log] -- Extracting keywords for searching documents.")         
            self.keywords = self._build_keywords_from_prompt(self.prompt)

        # Retrive documents
        print("[Runtime Log] -- Retriving relavant documents")
        information_retrived = []
        for _, (name, table) in tqdm(self.media_contents.items()):
            queris = self._retrive_information_from_table(self.keywords, table, n=200)
            information_retrived.append((name, queris))

        # Building prompts
        prompts = []
        for name, data in information_retrived:
            prompt = f"I want you to perform an anlysis on a telegram media called: {name} based on a user input prompt and some selected content/messages sent to this media.\n\n"\
            f"**User prompt: {self.prompt}**\n\nMessages:\n"
            for i, message in enumerate(data[len(data)-1:0:-1]):
                prompt = prompt + f'{i+1}) {message}\n'
                if len(prompt) > 200_000:
                    break
            prompts.append(prompt + '\n**Please perform the requested analysis in one Persian paragraph in maximum 1000 words.**')
        
        # Calling llm
        responses = []
        print("[Runtime Log] -- Calling LLM Api ...")
        for prompt in tqdm(prompts):
            response = call_llm(prompt)
            responses.append(response)
            time.sleep(30)

        # Generate final output
        print("[Runtime Log] -- Generating final output ...")
        final_prompt = f"I want you to conclude a requested analysis based on a user prompt. Below is first the user prompt (requested analysis) and then the partial analysis . Each "\
        f"partial analysis is the result of the analysis of the same prompt, but for a specifc media. I want you to conclude all these analysis and produce the final response to the prompt "\
        f"based on these partial analysis.\n\n**User prompt: {self.prompt}**\n\nPartial anlysis:\n"
        for i, response in enumerate(responses):
            final_prompt += f'{i+1}) {response}\n'
        final_prompt += "\nPlease write a paragraph in Persian language with maximum 1500 words."
        final_output = call_llm(final_prompt)
        return final_output
    


    def _build_keywords_from_prompt(self, prompt):
        prompt = f"I want to perform an analysis on telegram media. Please tell me the 5 best keywords to match the user prompt for keyword search inside the documents.\n\n**User prompt : {prompt}**\n\n"\
        f"The output format must be like:\nkw_1,kw_2,kw_3,kw_4,kw_5\n\nDo not output any extra text. Just 5 Persian keywords for this prompt to search for."
        keywords = call_llm(prompt)
        keywords = keywords.split(",")
        time.sleep(20)
        return keywords


    def _retrive_information_from_table(self, keywords, table, n=100):
        keyword_set = set([kw.lower() for kw in keywords])
        def score_text(text):
            if not isinstance(text, str) or not text.strip():
                return 0
            words = set(text.lower().split())
            overlap = keyword_set.intersection(words)
            return min(len(overlap), 5)  # cap at 5
        
        df = table.copy()
        df["score"] = df["cleaned_text"].apply(score_text)
        top_df = df[df["score"] > 0].sort_values("score", ascending=False).head(n)
        return top_df["cleaned_text"].tolist()


class TimeBasedOriented:
    def __init__(self, prompt, media_idx, start_date, end_date, from_trend=False):
        self.prompt = prompt 
        self.media_content = get_media_table_from_code(media_idx)
        self.media_content = filter_dataframe_by_date(self.media_content, start_date, end_date)
        self.from_trend = from_trend

    def run(self):
        if not self.from_trend:
            print("[Runtime Log] -- Requested anlysis started on pipeline 3.")

        # Generating prompts
        print("[Runtime Log] -- Retriving data...")
        prompt_header = "I want you to perform an analysis on a telegram media based on a user input prompt (requested analysis) and the content/messages sent to "\
        f"that media. The main goal is to determine what were the topics people usually talked about in telegram during a time period. Below is first the user prompt "\
        f"and then the messages sent to the target media.\n\n**User prompt: {self.prompt}**\n\nMessages:\n"
        prompts = []
        prompt = prompt_header
        for j, i in enumerate(range(len(self.media_content))):
            text = self.media_content.iloc[i]['cleaned_text']
            if not isinstance(text, str):
                continue
            if count_persian_letters(text) < 10:
                continue
            
            prompt += f"{i+1}){text}\n"
            if len(prompt) > 200_000:
                prompts.append(prompt + "\n\n**Now please do the analysis the user want in one Persian paragraph with maximum 500 words**")
                prompt = prompt_header

            
        # Call llm
        print(f"[Runtime Log] -- Calling LLM Api ...")
        responses = []
        for prompt in tqdm(prompts):
            response = call_llm(prompt)
            responses.append(response)
            time.sleep(60)
        
        # Generate final response
        final_prompt = "I want you to perform an analysis on a telegram media based on a user prompt and partial result. The partial results are the same analysis but on a "\
        f"smaller part of the whole data. I want you to conclude these partial results and tell what were the messages usually about in the target media. Below is first the "\
        f"user prompt and then the partial anlalysis:\n\n**User prompt: {self.prompt}**\n\n"
        for i, response in enumerate(responses):
            final_prompt += f"partial {i+1}){response}\n"
        if not self.from_trend:
            final_prompt += "\n**Please perform the requested analysis in one Persian paragraph with maximum 300 words.**"
        else:
            final_prompt += "\n**Please detect the trend and hot topics based on the contents and finally list them. Your output must be in Persian language**"
        final_output = call_llm(final_prompt)
        return final_output


class TrendDetection:
    def __init__(self, media_idx, start_date, end_date):
        self.inner_tbo = TimeBasedOriented("لطفا ترند ها و موضوعات داغ رسانه {} را از درون محتوای آن استخراج کن و آنها را لیست کن . ", media_idx, start_date, end_date, from_trend=True)
    def run(self):
        print("[Runtime Log] -- Requested anlysis started on pipeline 4.")
        return self.inner_tbo.run()


class IndividualPersonAnalysis:
    def __init__(self, prompt, media_idx, user_id):
        self.prompt = prompt
        self.user_id = user_id
        self.media_idx = media_idx
        #dir_root = dirname(dirname(abspath(__file__)))
        #users_file = os.path.join(dir_root, "media", "users.pkl")
        #if not os.path.exists(users_file):
        #    print("[Runtime Log] -- Generating users file...")
        #    extract_users_from_groups()
        
        #with open(users_file, 'rb') as f:
        #    self.users = pickle.load(f)

    def extract_user_messages(self, media_idx, user_id):
        table = get_media_table_from_code(media_idx)
        rows = table[table["sender_id"] == user_id]['cleaned_text']
        return rows.tolist()
    
    def run(self):
        print("[Runtime Log] -- Extracting user meesages ... ")
        user_messages = self.extract_user_messages(self.media_idx, self.user_id)
        print(f"[Runtime Log] -- Total number of the user messages: {len(user_messages)}")
        prompt = f"I want you to analyse person by the messages he/she has sent to a telegram group based on a user input prompt. Below is "\
        f"first the user prompt and then the messages this user has sent to the group.\n\n**User prompt: {self.prompt}**\n\nMessages of this person:\n"

        user_messages = sample(user_messages, min(1000, len(user_messages)))
        for i, m in enumerate(user_messages):
            prompt += f"{i+1}){m}\n"
        prompt += "\n**Please perform the required analysis on this user in one Persian Paragraph with maximum 500 words**"

        print("[Runtime Log] -- Calling LLM Api ...")
        final_output = call_llm(prompt)
        return final_output


class StatisticalInformation:
    def __init__(self, media_idx):
        self.media_idx = media_idx
        self.media_name = get_media_name_from_code(media_idx)
        self.media_content = get_media_table_from_code(media_idx)
        self.build_time_histogram()
        self.plot_date_charts()

    def build_time_histogram(self, bins=24):
        output_path = os.path.join(dir_root, 'application', 'resources', 'time_distro.png')
        times = pd.to_datetime(self.media_content["time"], format="%H:%M:%S", errors="coerce").dt.hour
        times = times.dropna()
        sns.set_theme(style="darkgrid")
        plt.figure(figsize=(10, 6))
        sns.histplot(times, bins=24, kde=False, color=sns.color_palette("magma", 24)[10])
        plt.title("Distribution of Times (by Hour)", fontsize=18, weight='bold', color="#333333")
        plt.xlabel("Hour of Day (0–23)", fontsize=14)
        plt.ylabel("Frequency", fontsize=14)
        plt.xticks(range(24))
        plt.yticks(fontsize=12)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"✅ Histogram saved as {output_path}")

    def plot_date_charts(self, output_prefix="date_charts"):
        df = self.media_content
        if "date" not in df.columns:
            raise ValueError("The dataframe must contain a 'date' column.")
        dates = pd.to_datetime(df["date"], format="%d/%m/%y", errors="coerce")
        df = df.assign(year=dates.dt.year, month=dates.dt.month, month_year=dates.dt.to_period("M"))
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(6, 6))
        df["year"].value_counts().sort_index().plot.pie(autopct="%1.1f%%", colors=sns.color_palette("tab20"))
        plt.title("Distribution of Years")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(os.path.join(dir_root, "application", "resources", f"{output_prefix}_years_pie.png"), dpi=300)
        plt.close()
        plt.figure(figsize=(6, 6))
        df["month"].value_counts().sort_index().reindex(range(1, 13), fill_value=0).plot.pie(
            autopct="%1.1f%%", labels=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
            colors=sns.color_palette("tab20c"))
        plt.title("Distribution of Months")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(os.path.join(dir_root, "application", "resources", f"{output_prefix}_months_pie.png"), dpi=300)
        plt.close()
        plt.figure(figsize=(12, 6))
        df["month_year"].value_counts().sort_index().plot(kind="bar", color=sns.color_palette("viridis", len(df["month_year"].unique())))
        plt.title("Histogram of Records per Month-Year")
        plt.xlabel("Month-Year")
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(dir_root, "application", "resources", f"{output_prefix}_month_year_hist.png"), dpi=300)
        plt.close()
        plt.figure(figsize=(12, 6))
        df.groupby("month_year").size().sort_index().plot(kind="line", marker="o", color="purple")
        plt.title("Records per Month Over Time")
        plt.xlabel("Month-Year")
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(dir_root, "application", "resources", f"{output_prefix}_time_series.png"), dpi=300)
        plt.close()
        print(f"✅ Charts saved with prefix '{output_prefix}'")


class Reporting:
    pass
