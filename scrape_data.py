import requests
from bs4 import BeautifulSoup
import pandas as pd
import math
import warnings
warnings.filterwarnings("ignore")

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
        'round': round_,#Changed: Earlier round was giving the object function but mapped to round_ in which we have fetched values
        'pick': pick,
        'college': college
    })
    
    other_df=pd.DataFrame(0,index=range(num_players),columns=range(49))
    # Need to discuss 
    '''
    Alert
    other_df = pd.DataFrame(0, index=range(num_players), columns=cols)

    '''
    other_df.iloc[:, 0] = range(1, num_players + 1)
    #Need to Discuss Part 2
    '''
    other_df.drop(["Row", "Name", "Position", "Round", "Pick", "College"],axis=1,inplace=True)
    '''
    other_df.rename(columns={0: 'Row'}, inplace=True)
    info_df.rename(columns={0: 'Row'}, inplace=True)  
    df = pd.merge(info_df, other_df, on='Row')
    cols = df.columns.tolist()
    df.columns = cols
    cols.remove('Row')
    df = df.drop(columns=['Row'])
    # print(df.head())
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
        # Read vital data
        pos = df.loc[row, "pos"]
        height = stats.loc[row, "Ht"]
        weight = stats.loc[row, "Wt"]  
        if type(height)==float and math.isnan(height):
            height='0-0'
        if type(weight)==float and math.isnan(weight):
            weight='000'
            
        hgt=height.split('-')
        df.loc[row, "Height"] = 12 * int(hgt[0]) + int(hgt[1])
        df.loc[row, "Weight"] = int(weight[:3])

        # *****Niketan******


        df.loc[row,5] = float(stats.loc[row, "40yd"])
        vertical=float(stats.loc[row,"Vertical"])
        if math.isnan(vertical):
            vertical=0.0
        
        df.loc[row,6]=vertical
        bench=float(stats.loc[row,"Bench"])
        if math.isnan(bench):
            bench=0

        df.loc[row,7]=bench
        broad_jump=float(stats.loc[row,"Broad Jump"])
        if math.isnan(broad_jump):
            broad_jump=0
        df.loc[row,8]=broad_jump
        three_cone=float(stats.loc[row,"3Cone"])
        if math.isnan(three_cone):
            three_cone=0.0
        df.loc[row,9]=three_cone
        shuttle=float(stats.loc[row,"Shuttle"])
        if math.isnan(shuttle):
            shuttle=0.0
        df.loc[row,10]=shuttle        
      

        df.rename(columns={5:"40yd",6:"Bench",7:"Broad Jump",8:"3Cone",9:"Shuttle"},inplace=True)

        if ((pos == "T") or (pos == "LS") or (pos == "G") or (pos == "C")):
            continue
        if len(stat_url)==0:
            bad_rows.append(row)

        # special case of broken links
        if (stat_url == "https://www.sports-reference.com/cfb/players/walter-thurmond-1.html"):
            stat_url = "https://www.sports-reference.com/cfb/players/walter-thurmond-iii-1.html"

        if (stat_url == "https://www.sports-reference.com/cfb/players/jj-watt-2.html"):
            stat_url = "https://www.sports-reference.com/cfb/players/jj-watt-1.html"
    
        if (stat_url == "https://www.sports-reference.com/cfb/players/donta-hightower-2.html"):
            stat_url = "https://www.sports-reference.com/cfb/players/donta-hightower-1.html"
    
        if (stat_url == "https://www.sports-reference.com/cfb/players/jr-sweezy-2.html"):
            stat_url = "https://www.sports-reference.com/cfb/players/jr-sweezy-1.html"
    
        if (stat_url == "https://www.sports-reference.com/cfb/players/louis-nix-iii.html"):
            stat_url = "https://www.sports-reference.com/cfb/players/louis-nix-iii-1.html"
        
        response = requests.get(stat_url)
        stat_page = BeautifulSoup(response.text, 'html.parser')
        conf_html = stat_page.select("tbody .left+ .left")
        conf = [conf.get_text() for conf in conf_html]
        conf = [value for value in conf if value != ""]
        if len(conf)>0:
            df.loc[row,1]=conf[-1]
        df.rename(columns={1:"Conference"},inplace=True)
           
        # Get all other stats
        pass_table = None
        punt_table = None
        kick_table = None
        rush_table = None
        def_table = None
        games = {}
        RB = True
        # print(pos)
        if (pos == "QB"):
            pass_table =clean_data(get_stat(stat_page, "passing"))
        if (pos in off_pos):
            rush_table=clean_data(get_stat(stat_page,"rushing"))
            if len(rush_table)==0:
                rush_table=clean_data(get_stat(stat_page,"receiving"))
                RB=False
        elif(pos in def_pos):
          def_table=clean_data(get_stat(stat_page,"defense"))
        #   print(get_stat(stat_page,"defense").columns)
        #   print(def_table)
          games=def_table.iloc[:,[5]]
          '''
          /****** Alert there is some issue with header function as i am not able to fetch the column names in  the dataframe returned from the function
          hence using.iloc to map the position of G as of now 
          '''    
        else:
            kick_table=clean_data(get_stat(stat_page,"kicking"))
            if kick_table is None:
                kick_table=clean_data(get_stat(stat_page,"punting"))
            games=kick_table.iloc[:,[5]]
        ret_table=clean_data(get_stat(stat_page,"punt_ret"))

        if ret_table is None:
            ret_table=clean_data(get_stat(stat_page,"kick_ret"))
        
        # print(games)


        #/********* Niketan Ends here********/

        #/********* Aarsh Starts here********/
        games = [g for g in games if pd.notna(g)]
        games = list(map(float, games))
        
        # Calculate sum of games and number of seasons
        df.loc[row, "Games"] = sum(games)
        df.loc[row, "Seasons"] = len(games)

        if ((pass_table is not None) and (len(pass_table) > 0)):
            df.loc[row, "Pass Att"] = pass_table.iloc[-1]["Att"]
            df.loc[row, "Pass Completions"] = pass_table.iloc[-1]["Cmp"]
            df.loc[row, "Pass Yds"] = pass_table.iloc[-1]["Yds"]
            df.loc[row, "Pass TD"] = pass_table.iloc[-1]["TD"]
            df.loc[row, "Pass Int"] = pass_table.iloc[-1]["Int"]
            df.loc[row, "Passer Rating"] = pass_table.iloc[-1]["Rate"]

        if ((rush_table is not None) and (len(rush_table) > 0)):
            if RB:  # Running back
                df.loc[row, "Rush Att"] = rush_table.iloc[-1][7]
                df.loc[row, "Rush Yds"] = rush_table.iloc[-1][8]
                df.loc[row, "Rush TD"] = rush_table.iloc[-1][10]
                df.loc[row, "Rec"] = rush_table.iloc[-1][11]
                df.loc[row, "Rec Yds"] = rush_table.iloc[-1][12]
                df.loc[row, "Rec TD"] = rush_table.iloc[-1][14]
            else:
                df.loc[row, "Rush Att"] = rush_table.iloc[-1][11]
                df.loc[row, "Rush Yds"] = rush_table.iloc[-1][12]
                df.loc[row, "Rush TD"] = rush_table.iloc[-1][14]
                df.loc[row, "Rec"] = rush_table.iloc[-1][7]
                df.loc[row, "Rec Yds"] = rush_table.iloc[-1][8]
                df.loc[row, "Rec TD"] = rush_table.iloc[-1][10]

        # if ((def_table is not None) and (len(def_table) > 0)):
            df.loc[row, "Solo Tackles"] = def_table.iloc[-1][18]
            df.loc[row, "Ast Tackles"] = def_table.iloc[-1][19]
            df.loc[row, "Total Tackles"] = def_table.iloc[-1][20]
            df.loc[row, "Tackles for Loss"] = def_table.iloc[-1][21]
            df.loc[row, "Sacks"] = def_table.iloc[-1][22]
            df.loc[row, "Int"] = def_table.iloc[-1][23]
            df.loc[row, "Int Return Yards"] = def_table.iloc[-1][24]
            df.loc[row, "Int TD"] = def_table.iloc[-1][25]
            # df.loc[row, "Pass Deflection"] = def_table.iloc[-1]["PD"]
            # df.loc[row, "Fumble Recovery"] = def_table.iloc[-1]["FR"]
            # df.loc[row, "Fumble Return Yards"] = def_table.iloc[-1][18]
            # df.loc[row, "Fumble TD"] = def_table.iloc[-1][19]
            # df.loc[row, "Forced Fumbles"] = def_table.iloc[-1]["FF"]

        if ((ret_table is not None) and (len(ret_table) > 0)):
            df.loc[row, "KRs"] = ret_table.iloc[-1][7]
            df.loc[row, "KR Yds"] = ret_table.iloc[-1][8]
            df.loc[row, "KR TD"] = ret_table.iloc[-1][10]
            df.loc[row, "PRs"] = ret_table.iloc[-1][11]
            df.loc[row, "PR Yds"] = ret_table.iloc[-1][12]
            df.loc[row, "PR TD"] = ret_table.iloc[-1][14]

        if ((kick_table is not None) and (len(kick_table) > 0)):
            if pos == "K":
                df.loc[row, "XPA"] = kick_table.iloc[-1][8]
                df.loc[row, "XP%"] = kick_table.iloc[-1][9]
                df.loc[row, "FGA"] = kick_table.iloc[-1][11]
                df.loc[row, "FG%"] = kick_table.iloc[-1][12]
                df.loc[row, "Punts"] = kick_table.iloc[-1][14]
                df.loc[row, "Punt Avg"] = kick_table.iloc[-1][16]
            elif pos == "P":
                df.loc[row, "XPA"] = kick_table.iloc[-1][11]
                df.loc[row, "XP%"] = kick_table.iloc[-1][12]
                df.loc[row, "FGA"] = kick_table.iloc[-1][14]
                df.loc[row, "FG%"] = kick_table.iloc[-1][15]
                df.loc[row, "Punts"] = kick_table.iloc[-1][7]
                df.loc[row, "Punt Avg"] = kick_table.iloc[-1][9]

        # df.to_csv('combine_data.csv',index=False)
        break
    break
   