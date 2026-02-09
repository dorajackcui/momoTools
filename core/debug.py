import pandas as pd
filepath = r''
debug_key1 = "4D03332141C5B492D7E97891939EDDFB"
debug_key2 = "test1"
df = pd.read_excel(filepath, keep_default_na=False)
filtered_df = df[df['Key'] == debug_key1]
print(filtered_df['MsgStr'])
