import re
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from io import TextIOWrapper


@dataclass
class LanguageConsts:
    unicode_direction_mark_char: str
    date_pattern_regex: str
    date_format: str
    attached_file_text: str


hebrew = LanguageConsts(
    unicode_direction_mark_char="\u200f",
    date_pattern_regex=r"\[\d{1,2}.\d{2}.\d{4}, \d{1,2}:\d{2}:\d{2}\]",
    date_format="[%d.%m.%Y, %H:%M:%S]",
    attached_file_text="מצורף",
)
english = LanguageConsts(
    unicode_direction_mark_char="\u200e",
    date_pattern_regex=r"\[\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2}:\d{2}\]",
    date_format="[%d/%m/%y, %H:%M:%S]",
    attached_file_text="attached",
)


def detect_language(fobj: TextIOWrapper):
    """Detects the language of the chat file.
    Returns a LanguageConsts object.
    """
    first_line = fobj.readline()
    fobj.seek(0)
    if hebrew.unicode_direction_mark_char in first_line:
        return hebrew
    elif english.unicode_direction_mark_char in first_line:
        return english
    else:
        raise ValueError("Language not supported")


def parse_chat_file(filepath: str):
    """Parses a WhatsApp chat file.
    Returns a pandas DataFrame.
    """
    with open(filepath, "r", encoding="utf-8") as fobj:
        language = detect_language(fobj)
        data = fobj.read()

    # Ignore the unicode direction mark char, if exists, and match the date pattern.
    # We do it differently for each function, because capture groups act weird on "re.split()"

    # pass the pattern and data to split it to get the list of messages
    messages = re.split(
        f"{language.unicode_direction_mark_char}?{language.date_pattern_regex}", data
    )[1:]
    # extract all dates
    dates = re.findall(
        f"{language.unicode_direction_mark_char}?({language.date_pattern_regex})", data
    )

    df = pd.DataFrame({"user_message": messages, "message_date": dates})

    # convert message_date type
    df["message_date"] = pd.to_datetime(df["message_date"], format=language.date_format)
    df.rename(columns={"message_date": "date"}, inplace=True)

    # separate Users and Message
    users = []
    messages = []
    for message in df["user_message"]:
        entry = re.split("([\w\W]+?):\s", message)
        if entry[1:]:  # user name
            users.append(entry[1])
            messages.append(" ".join(entry[2:]))
        else:
            users.append("group_notification")
            messages.append(entry[0])
    df["user"] = users
    df["message"] = messages
    df.drop(columns=["user_message"], inplace=True)

    # Extract multiple columns from the Date Column
    df["only_date"] = df["date"].dt.date
    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.month_name()
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute

    file_name = (
        df.message.str.extract(f"<{language.attached_file_text}(.*?)>")
        .loc[:, 0]
        .str.strip()
        .rename("file_name")
    )

    chat = df.join(file_name)  # .join(attachment)

    # chat["has_whatsapp_metadata"] = df.message.str.find(
    #     language.unicode_direction_mark_char
    # ).ge(0)

    chat.to_csv("./chat.csv", index=False)

    return chat


parse_chat_file("CivilChat/_chat.txt")
