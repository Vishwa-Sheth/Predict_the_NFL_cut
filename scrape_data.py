import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_stat(html_data, stat):
    """
    Given HTML data and a stat, returns the value of the stat.
    """
    stat_id = f"#{stat}"
    all_stat_id = f"#all_{stat}"
    node = html_data.select_one(stat_id)
    if node:
        return pd.read_html(str(node))[0]
    else:
        node = html_data.select_one(all_stat_id)
        if node:
            comment = next(filter(lambda x: x.is_comment, node.contents))
            return pd.read_html(comment)[0]
        else:
            return None

def clean_data(final_table):
    """
    Cleans the data from get_stat.
    """
    if final_table is not None:
        final_table.columns = final_table.iloc[0]
        final_table = final_table.drop(0)
        return final_table
    else:
        return None

# Loop over all years in the dataset.
current = False
START_YEAR = 2012
END_YEAR = 2022

for year in range(START_YEAR, END_YEAR + 1):
    print(year)
    # Read draft data
    url = f"https://www.pro-football-reference.com/draft/{year}-combine.htm"
    response = requests.get(url)
    webpage = BeautifulSoup(response.text, 'html.parser')
    
    # Get the names of the players
    names_html = webpage.select("tbody .left:nth-child(1)")
    all_names = [name.get_text() for name in names_html]
    names = [name for name in all_names if name != "Player"]
    num_players = len(names)
    
    # Get the position of the players
    pos_html = webpage.select("th+ td")
    pos = [pos.get_text() for pos in pos_html]
    
    pick = [0] * num_players
    round_ = [0] * num_players
    # Get draft data if this is not the current year.
    if not current:
        draft_html = webpage.select(".right+ .left")
        draft_info = [info.get_text() for info in draft_html]
        draft_info = ["Undrafted / 0th / 0th / 0" if info == "" else info for info in draft_info]
        draft_spots = [info.split(" / ") for info in draft_info]
        round_ = [int(spot[1][0]) for spot in draft_spots]
        pick = [int(''.join(filter(str.isdigit, spot[2]))) for spot in draft_spots]
