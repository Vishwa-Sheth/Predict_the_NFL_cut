import requests
from bs4 import BeautifulSoup
import pandas as pd
import math

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
END_YEAR = 2023

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

    #Get college data
    college_elements = webpage.select('td.left + .left')
    college = [element.get_text() for element in college_elements]

    # Define names of columns
    cols = ["Row", "Name", "Position", "Round", "Pick", "College", "Conference", "Games", "Seasons"]
    combine = ["Height", "Weight", "40 Yard", "Bench", "Broad Jump", "Shuttle", "3 Cone", "Vertical"]
    defense = ["Solo Tackles", "Ast Tackles", "Total Tackles", "Tackles for Loss", "Sacks", "Int", "Int Return Yards", "Int TD", "Pass Deflection", "Fumble Recovery", "Fumble Return Yards", "Fumble TD", "Forced Fumbles"]
    offense = ["Pass Att", "Pass Completions", "Pass Yds", "Pass TD", "Pass Int", "Passer Rating", "Rush Att", "Rush Yds", "Rush TD", "Rec", "Rec Yds", "Rec TD"]
    special = ["PRs", "PR Yds", "PR TD", "KRs", "KR Yds", "KR TD", "XPA", "XP%", "FGA", "FG%", "Punts", "Punt Avg"]
    cols += combine + offense + defense + special

    # List names of positions
    def_pos = ["CB", "DB", "DE", "DT", "FS", "ILB", "LB", "NT", "OLB", "S", "SS", "EDGE"]
    off_pos = ["C", "FB", "G", "QB", "RB", "T", "TE", "WR"]
    other_pos = ["K", "P", "LS"]

    # Set up dataframe that holds the data.
    info_df = pd.DataFrame({
        'Row': range(1, num_players + 1),
        'names': names,
        'pos': pos,
        'round': round,
        'pick': pick,
        'college': college
    })

    other_df = pd.DataFrame(0, index=range(num_players), columns=range(49))
    other_df.iloc[:, 0] = range(1, num_players + 1)
    other_df.rename(columns={0: 'Row'}, inplace=True)
    info_df.rename(columns={0: 'Row'}, inplace=True)
    
    df = pd.merge(info_df, other_df, on='Row')
    cols = df.columns.tolist()
    df.columns = cols
    cols.remove('Row')
    df = df.drop(columns=['Row'])

    # Get list of stat pages for all players
    stat_urls = [link.get('href') for link in webpage.select('.left + .right a')]
    tables = webpage.find_all('table')
    if tables:
        stats = pd.read_html(str(tables[0]))[0]
    stats = stats[stats['Player'] != 'Player']
    stats.reset_index(drop=True, inplace=True)

    bad_rows = []
    for row in range(len(df)):
        # Skip header rows
        if df.loc[row, "names"] == "Player":
            bad_rows.append(row)
            continue
        
        stat_url = stat_urls[0]
        #html_nodes(stat_urls[row], "a")[0].get("href")

        # Read vital data
        pos = df.loc[row, "pos"]
        height = stats.loc[row, "Ht"]
        weight = stats.loc[row, "Wt"]
        
        # print(height, type(height))
        #print(weight)
        
        if type(height)==float and math.isnan(height):
            height='0-0'
        if type(weight)==float and math.isnan(weight):
            weight='000'
            
        hgt=height.split('-')
        
        #height = list(map(int, height.split("-")))
        df.loc[row, "Height"] = 12 * int(hgt[0]) + int(hgt[1])
        df.loc[row, "Weight"] = int(weight[:3])
    print(df)