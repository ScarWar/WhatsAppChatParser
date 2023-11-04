import re
import pandas as pd
from pathlib import Path

# read the text file
chat_file = Path("CivilChat/_chat.txt")
data = chat_file.read_text(encoding='utf-8')
# print(type(data))

# regular expression to find the dates
# This will help us split each message
pattern = r'\[\d{1,2}.\d{2}.\d{4}, \d{1,2}:\d{2}:\d{2}\]'

# pass the pattern and data to split it to get the list of messages
messages = re.split(pattern, data)[1:]

# extract all dates
dates = re.findall(pattern, data)

# create dataframe
df = pd.DataFrame({'user_message': messages, 'message_date': dates})

# convert message_date type
df['message_date'] = pd.to_datetime(df['message_date'],
                                    format='[%d.%m.%Y, %H:%M:%S]')
df.rename(columns={'message_date': 'date'}, inplace=True)
# df.head(4)

# separate Users and Message
users = []
messages = []
for message in df['user_message']:
    entry = re.split('([\w\W]+?):\s', message)
    if entry[1:]:  # user name
        users.append(entry[1])
        messages.append(" ".join(entry[2:]))
    else:
        users.append('group_notification')
        messages.append(entry[0])

df['user'] = users
df['message'] = messages
df.drop(columns=['user_message'], inplace=True)

# Extract multiple columns from the Date Column
df['only_date'] = df['date'].dt.date
df['year'] = df['date'].dt.year
df['month_num'] = df['date'].dt.month
df['month'] = df['date'].dt.month_name()
df['day'] = df['date'].dt.day
df['day_name'] = df['date'].dt.day_name()
df['hour'] = df['date'].dt.hour
df['minute'] = df['date'].dt.minute

# find file attachments
file_name = (
    df[df.message.str.find('מצורף').ge(0)]
    .message.str.extract(r'<(.*?)>')
    .loc[:, 0].str[5:]
    .str.strip()
    .rename('file_name')
)
chat_folder = chat_file.parent

attachment = (
    file_name
    .map(lambda file_name: (chat_folder / file_name).read_bytes())
    .rename('attachment')
)

chat = df.join(file_name).join(attachment)

chat.to_pickle('./chat.pkl')
