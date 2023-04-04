import streamlit as st
import pandas as pd
import subprocess
import datetime
import pathlib
from pathlib import Path 
import plotly.express as px
import plotly.graph_objects as go
import kaggle
from st_aggrid import AgGrid
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode, AgGridTheme

#Kaggle API connection
kaggle.api.authenticate()
kaggle.api.dataset_download_files('daily-steam-sales', unzip=True)

st.set_page_config(layout="wide")
df_raw = pd.read_json("steamgames.json")


@st.cache_data()
def load_data(df_raw):
    #Convert columns orig_price and disc_price to float
    df_raw.orig_price = df_raw.orig_price.astype(float)
    df_raw.disc_price = df_raw.disc_price.astype(float)

    # Separate recent_reviews and general_revies from reviews
    df_raw[['recent_reviews', 'general_reviews', 'borrar', 'borrar1']] = pd.DataFrame(df_raw.reviews.tolist(), index= df_raw.index)
    #For some reason it creates 2 more empty columns, so just delete them
    del df_raw['borrar']
    del df_raw['borrar1']
    # Get just the percentage numbers from the reviews
    df_raw['recent_reviews'] = df_raw['recent_reviews'].str.extract('(\d+)%', expand=True)
    df_raw['general_reviews'] = df_raw['general_reviews'].str.extract('(\d+)%', expand=True)
    # Erase the % symbol
    df_raw['general_reviews'] = df_raw.general_reviews.replace(r'%', '', regex=True)
    df_raw['recent_reviews'] = df_raw.recent_reviews.replace(r'%', '', regex=True)
    # Transform to float
    df_raw.recent_reviews = df_raw.recent_reviews.astype(float)
    df_raw.general_reviews = df_raw.general_reviews.astype(float)

    #Separete tags from list to string separated with a space
    df_raw['tags'] = [','.join(map(str, l)) for l in df_raw['tags']]
    df_raw.tags = df_raw.tags.replace(r'\s+', '', regex=True)
    df_raw.tags = df_raw.tags.replace(r',', ' ', regex=True)
    # Get each tag as a new column, each game could have up to 20 different tags
    tag_columns = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18", "T19", "T20"]
    df_raw[tag_columns] = df_raw.tags.str.split(" ", expand=True)
    # Create a dataframe with the frequency of all tags
    df_tags = df_raw[tag_columns]
    sr_tag = df_tags.stack().value_counts().sort_index()
    sr_tag = sr_tag.sort_values(ascending=False)
    df_tags = pd.DataFrame({'tag':sr_tag.index, 'freq':sr_tag.values})
    # Create column with the price differences
    df_raw['dif_price'] = df_raw.orig_price - df_raw.disc_price

#Preprocessing to determine the best deals of the day
    #Get the games were it's general reviews are not Null
    df_best = df_raw[df_raw['general_reviews'].notnull()]
    #Get the games with general reviews are at least 80
    df_best = df_raw[df_raw['general_reviews'] >= 80]
    #Calculate the price-review ratio (made up formula)
    df_best['pr_ratio'] = df_best.dif_price * df_best.general_reviews 
    #Sort the dataframe in descending order
    df_best = df_best.sort_values(by='pr_ratio',ascending=False)

    df_free = df_raw[df_raw['disc_price']==0]
    
    return df_raw, df_tags, df_best.head(10), df_free



# Project title
icon = st.container()

# Explanation and motivation
intro =  st.container()
# Dataset info, how I collected the data?, why I collected the data?
data_info = st.container()

#Spider description, how the scrapper works
scrape = st.container()

# Table showing the complete and clean dataset
data = st.container()

# Games distribution by discount
# Games disttribution by tag
# Scatter disc_price vs orig_price
graphs = st.container()

top10= st.container()

with icon:
    left_col, center_col, right_col =st.columns([8,1,8])
    with center_col:
        steam_logo = st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=150) 

with intro:
    row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns(
        (0.01, 2, 1, 1, 0.01)
    )
    with row0_1:
        st.title('Analyzing steam sales of the day')

    with row0_2:
        
        st.subheader(
            "A Streamlit web app by [Hiram Cortes](https://www.linkedin.com/in/hdcortesd/)"
            )
        st.markdown("You can find the source code on my [GitHub](https://github.com/MaxPower14/streamlit-steam-app)")
    row1_1, row1_spacer2 = st.columns((4.2, 0.1))

    with row1_1:
        st.markdown(
            "Hey there! Welcome to Hiram's Steam sales Analysis App. This app scrapes daily the Steam games currently on sale and analyzes them, looking into different distributions of the data like discount, reviews and prices. Giving a breakdown by tag and taking a closer look on which conditions to look to land a better deal from a money saving perspective. After some intersting graphs, it gives to you the best price-quality deals with a simple formula that I came up to and the games currently free. Give it a go!"
        )
        st.markdown("⚠️ Notice: This dataset has not been curated to exclude NSFW titles, discretion is advised.")

with data:

    st.subheader('Today\'s data')    
    df, df_tags, df_best, df_free = load_data(df_raw)
    num_games = "I found " + str(len(df)) + " games on sale! " + " 🎮"
    st.markdown(num_games)
    tag_columns = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18", "T19", "T20"]
    clean_columns = ['name', 'discount', 'orig_price', 'disc_price', 'dif_price', 'recent_reviews', 'general_reviews', 'link']
    see_data = st.expander('Click here to see the raw data 👉')
    with see_data:
        st.dataframe(data=df[clean_columns + tag_columns])



with graphs:
    st.markdown('####')
    #Calculate the mean, max and min value for discount
    disc_avg = round(df.discount.mean(), 2)
    disc_max = df.discount.max()
    disc_min = df.discount.min()
    #Find the game name with the max and min value for discount
    games_max_disc = df[df["discount"] == disc_max]
    g_max_discount = games_max_disc["name"].iloc[0]
    games_min_disc = df[df["discount"] == disc_min]
    g_min_discount = games_min_disc["name"].iloc[0]

    #Calculate the mean, max and min value for dif_price
    dif_price_avg = round(df["dif_price"].mean())
    dif_price_max = df["dif_price"].max()
    dif_price_min = df["dif_price"].min()
    #Calculate the mean, max and min value for dif_price
    games_max_dif = df[df["dif_price"] == dif_price_max]
    g_max_dif = games_max_dif["name"].iloc[0]
    games_min_dif = df[df["dif_price"] == dif_price_min]
    g_min_dif = games_min_dif["name"].iloc[0]

    #Calculate the mean, max and min value for general reviews
    gen_rev_avg = round(df["general_reviews"].mean())
    gen_rev_max = df["general_reviews"].max()
    gen_rev_min = df["general_reviews"].min()
    #Calculate the mean, max and min value for general reviews
    games_max_general_reviews = df[df["general_reviews"] == gen_rev_max]
    g_max_general_reviews = games_max_general_reviews["name"].iloc[0]
    games_min_general_reviews = df[df["general_reviews"] == gen_rev_min]
    g_min_general_reviews = games_min_general_reviews["name"].iloc[0]

    #Calculate the mean, max and min value for recent reviews
    rec_rev_avg = round(df["recent_reviews"].mean())
    rec_rev_max = df["recent_reviews"].max()
    rec_rev_min = df["recent_reviews"].min()
    #Calculate the mean, max and min value for recent reviews
    games_max_recent_reviews = df[df["recent_reviews"] == rec_rev_max]
    g_max_recent_reviews = games_max_recent_reviews["name"].iloc[0]
    games_min_recent_reviews = df[df["recent_reviews"] == rec_rev_min]
    g_min_recent_reviews = games_min_recent_reviews["name"].iloc[0]

    #Get the most recurrent tag and its count
    max_tag = df_tags["tag"].iloc[0]
    max_tag_count = df_tags["freq"].iloc[0]
    min_tag = df_tags["tag"].iloc[len(df_tags)-1]
    min_tag_count = df_tags["freq"].iloc[len(df_tags)-1]    

    #Calculate the mean, max and min value for discount price
    disc_price_avg = round(df["disc_price"].mean())
    disc_price_max = df["disc_price"].max()
    disc_price_min = df["disc_price"].min()
    #Calculate the mean, max and min value for discount price
    games_max_disc_price = df[df["disc_price"] == disc_price_max]
    g_max_disc_price = games_max_disc_price["name"].iloc[0]
    games_min_disc_price = df[df["disc_price"] == disc_price_min]
    g_min_disc_price = games_min_disc_price["name"].iloc[0]

    #Calculate the mean, max and min value for original price
    org_price_avg = round(df["orig_price"].mean())
    org_price_max = df["orig_price"].max()
    org_price_min = df["orig_price"].min()
    #Calculate the mean, max and min value for original price
    games_max_org_price = df[df["orig_price"] == org_price_max]
    g_max_org_price = games_max_org_price["name"].iloc[0]
    games_min_org_price = df[df["orig_price"] == org_price_min]
    g_min_org_price = games_min_org_price["name"].iloc[0]

    #Calculate quantiles of dif_price
    q3 = df["dif_price"].quantile(0.75)
    q1 = df["dif_price"].quantile(0.25)
    iqr = q3-q1
    lower_range = round(q1 - (1.5 * iqr), 2)
    upper_range = round(q3 + (1.5 * iqr), 2)

    st.subheader('Analyzing today\'s data')    
    left_col, middle_col, right_col = st.columns((1,0.3,1))
    with left_col:        
        fig = px.histogram(df, x="discount", nbins=10, title="Games distribution by discount")
        st.write(fig)
        st.markdown("Looks like the average discount for today\'s games is **{} %**. The game with the minimum discount is **{} with {} %**  and the one with the biggest discount is **{} with {} %**.".format(
            disc_avg, g_min_discount, disc_min, g_max_discount, disc_max))
        st.markdown("##")
        fig = px.histogram(df, x="general_reviews", title="Games distribution by general reviews")
        st.write(fig)
        st.markdown("Looks like the average game on sale today has a general reviews score of **{} %**. The game with the lowest general reviews is **{}** with **{}%** and the game with the highest general reviews is **{}** with **{}%**".format(
            gen_rev_avg, g_min_general_reviews, gen_rev_min, g_max_general_reviews, gen_rev_max))
        fig = px.histogram(df, x="disc_price", nbins=40, title="Games distribution by discount price")
        st.write(fig)
        st.markdown("The average price after discount for today\'s games is \$**{}**. Being **{}** the one with the lowest discount price with \$**{}** and **{}** the one with the highest discount price with \$**{}**.".format(
            disc_price_avg, g_min_disc_price, disc_price_min, g_max_disc_price, disc_price_max
        ))
       
        fig = px.histogram(df, x="dif_price", nbins=40, title="Games distribution by saving price")
        st.write(fig)
        st.markdown("Here´s the distribution of how much money you could save up per game. On average, you can save up to  **\${}**. The game where you can save the most is **{} with  \$ {}**, and the game where you can save the least is **{} with  \$ {}**.".format(
            dif_price_avg, g_max_dif, dif_price_max, g_min_dif, dif_price_min
        ))

    with right_col:
        fig = px.bar(df_tags.head(15), x='tag', y='freq', title="Games distribution by tag")
        st.write(fig)
        st.markdown("The breakdown by tag for the games of today puts **{}** as the most recurrent tag on sale with **{}** games and the least recurrent tag is **{}** with **{}** game(s).".format(
            max_tag, max_tag_count, min_tag, min_tag_count
        ))
        fig =  px.histogram(df, x="recent_reviews", title="Games distribution by recent reviews")
        st.write(fig)
        st.markdown("Looks like the average game on sale today has a recent reviews score of **{} %**. The game with the lowest recent reviews is **{}** with **{}%** and the game with the highest recent reviews is **{}** with **{}%**".format(
            rec_rev_avg, g_min_recent_reviews, rec_rev_min, g_max_recent_reviews, rec_rev_max))        
        fig = px.histogram(df, x="orig_price", nbins=50, title="Games distribution by original price")
        st.write(fig) 
        st.markdown("The average price before discount for today\'s games is \$**{}**. Being **{}** the one with the lowest original price with \$**{}** and **{}** the one with the original discount price with \$**{}**.".format(
            org_price_avg, g_min_org_price, org_price_min, g_max_org_price, org_price_max
        ))        
        st.markdown("#")
        fig = px.box(df, y="dif_price", hover_name="name", hover_data=['general_reviews', 'orig_price', 'discount', 'disc_price'], title="Box plot for saving price")
        st.write(fig)
        st.markdown("A box plot may help us to determine if the money we may be saving is an unusual case (outliers) or not. For today\'s games, every game in which we are saving more than **\${}**, we can considered it as an unusual case and it could be a good idea considering buying it, at least from the money saving perspective.".format(
            upper_range
        ))
    



with top10:
    st.markdown('###')
    st.title('Top 10 deals of the day')
    left_col, right_col = st.columns(2)

    st.markdown("To determine the best deals I came up with a made up and simple formula: $qp = gr * sm$.")
    st.markdown("Where: ")
    st.markdown("- $qp = $ Quality-price")
    st.markdown("- $gr=$General Reviews")
    st.markdown("- $sm = $Saved Money (Original price $-$ discount price) ")
    st.markdown("I created this formula trying to quantify the quality-price trade off in order to find the best current deals. The next table shows the 10 games with the largest $qp$ from games with more than 80\% of General Reviews")

    st.markdown("⚠️ This formula is not meant to determine if a games is better than other. It just tries to give you the best deal from a money saving approach but still triyng to consider the reviews.")

    col_left, col_right = st.columns((1,0.095))
    with col_left:
        AgGrid(df_best[['name', 'general_reviews', 'discount', 'orig_price', 'disc_price', 'dif_price', 'link']], 
        
            theme='streamlit', columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)

    st.markdown('##')
    st.title('Games currently free')
    st.markdown("⚠️ Sometimes some of this games can be free to play only for the wekeend, I recommend you to double check on the Steam store.")
    col_left, col_right = st.columns((1,0.095))
    with col_left:
        AgGrid(df_free[['name', 'general_reviews', 'discount', 'orig_price', 'disc_price', 'dif_price', 'link']], 
            theme='streamlit', columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)





    