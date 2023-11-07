import zipfile
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
    date_pattern_regex=r"\[\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}:\d{2}\]",
    date_format="[%d/%m/%Y, %H:%M:%S]",
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


def output_file_path_to_attachment_dir_path(output_filepath: str):
    """Converts the output file path to the attachment directory path.
    Returns the attachment directory path.
    """
    path = Path(output_filepath).parent
    dir_name = Path(output_filepath).stem + "_attachments"
    return path / dir_name


def _parse_chat_file(extracted_zip_path: str, output_filepath: str):
    """Parses a WhatsApp chat file.
    Returns a pandas DataFrame.
    """
    chat_filepath = Path(extracted_zip_path) / "_chat.txt"

    with open(chat_filepath, "r", encoding="utf-8") as fobj:
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
    df.rename(columns={"message_date": "datetime"}, inplace=True)

    # separate Users and Message
    users = []
    messages = []
    for message in df["user_message"]:
        entry = re.split("([^:]+?):\s", message)
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
    df["date"] = df["datetime"].dt.date.astype(str)
    df["time"] = df["datetime"].dt.time.astype(str)
    df["datetime"] = df["datetime"].astype(str)

    file_name = (
        df.message.str.extract(f"<{language.attached_file_text}(.*?)>")
        .loc[:, 0]
        .str.strip()
        # Ignore NaN
        .fillna("")
        # Add the attachment directory path to the file name
        .apply(lambda x: Path(extracted_zip_path) / x if x else x)
        .rename("file_name")
    )

    chat = df.join(file_name)  # .join(attachment)

    # chat["has_whatsapp_metadata"] = df.message.str.find(
    #     language.unicode_direction_mark_char
    # ).ge(0)

    # chat.to_csv(output_filepath, index=False)

    # # Export to excel
    chat.to_excel(f"{output_filepath}.xlsx", index=None, header=True)

    return output_filepath


def extract_zip_file(filepath: str, output_dir_path: str):
    """Extracts a zip file to the given output directory path.
    Returns the output directory path.
    """
    output_dir_path = Path(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(filepath, "r") as zip_file:
        zip_file.extractall(output_dir_path)
    return output_dir_path


def parse_chat_file(filepath: str, output_filepath: str):
    """Parses a WhatsApp chat file.
    Returns a pandas DataFrame.
    """
    # Check if the filepath is "_chat.txt"
    if Path(filepath).name == "_chat.txt":
        extracted_path = Path(filepath).parent
    # Check if it's a directory
    elif Path(filepath).is_dir():
        extracted_path = Path(filepath)
    elif zipfile.is_zipfile(filepath):
        extracted_path = extract_zip_file(
            filepath, output_file_path_to_attachment_dir_path(output_filepath)
        )
    else:
        raise ValueError("Invalid file path")

    return _parse_chat_file(extracted_path, output_filepath)
