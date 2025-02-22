from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
from faicons import icon_svg
from shinywidgets import render_plotly
from state_choices import STATE_CHOICES

from shiny import reactive
from shiny.express import input, render, ui

# ---------------------------------------------------------------------
# Reading in Files
# ---------------------------------------------------------------------
# Define the path to the "data" folder
data_folder = Path(__file__).parent / "Data"

# Read CSV files from the "data" folder
new_listings_df = pd.read_csv(data_folder / "ZillowDataNewListingsto2025.csv")
median_listing_price_df = pd.read_csv(data_folder / "ZillowDataMedianListPricetoJan2025.csv")
for_sale_inventory_df = pd.read_csv(data_folder / "ZillowDataInventorytoJan2025.csv")

# ---------------------------------------------------------------------
# Helper functions - converting to DateTime
# ---------------------------------------------------------------------
def string_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def filter_by_date(df: pd.DataFrame, date_range: tuple):
    rng = sorted(date_range)
    dates = pd.to_datetime(df["Date"], format="%Y-%m-%d").dt.date
    return df[(dates >= rng[0]) & (dates <= rng[1])]

# Use ctrl + tilda toggle the terminal box at the bottom of the screen.
# ---------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------

# for_sale_inventory_df2 = for_sale_inventory_df['StateName'].fillna('United States')
# for_sale_inventory_df2 = for_sale_inventory_df['StateName'].drop_duplicates()
# for_sale_inventory_df2 = for_sale_inventory_df2.sort_values().tolist()

# CSS styling

ui.tags.style(
    """
    .modebar{
        display: none;

    }
    body {
        background-color: lightblue;
    }
    """
)

# Code begins:

ui.page_opts(title = 'US Housing App From Zillow Data (up to Jan 2025)', fillable=False)


with ui.sidebar(bg="#f8f8f8", open='open'):

    ui.input_select('state', 'Filter By State', STATE_CHOICES)
    ui.input_select('city', 'Filter By City', choices=[])  # Initially empty, updated dynamically
    ui.input_slider("date_range","Filter by Date Range",
                min = string_to_date("2020-1-31"),
                max = string_to_date("2025-1-31"),
                value = [string_to_date(x) for x in ["2020-1-31","2025-1-31"]])
    

with ui.layout_column_wrap():
    with ui.value_box(showcase = icon_svg("dollar-sign")):
        "Current Median List Price (State)"

        @render.ui
        def price():
            date_columns = median_listing_price_df.columns[6:]
            states = median_listing_price_df.groupby("StateName").mean(numeric_only=True)
            dates = states[date_columns].reset_index()
            states = dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")
            country = median_listing_price_df[median_listing_price_df["RegionType"] == "country"]
            country_dates = country[date_columns].reset_index()
            country_dates["StateName"] = "United States"
            country = country_dates.melt(
                id_vars=["StateName"], var_name="Date", value_name="Value"
            )

            res = pd.concat([states, country])

            res = res[res["Date"] != "index"]

            df = res[res["StateName"] == input.state()]

            last_value = df.iloc[-1,-1]
            return f"${last_value:,.0f}"
        
    with ui.value_box(showcase = icon_svg("house")):
        "Home Inventory % Change (State)"
        @render.ui
        def change():
            date_columns = median_listing_price_df.columns[6:]
            states = median_listing_price_df.groupby("StateName").mean(numeric_only=True)
            dates = states[date_columns].reset_index()
            states = dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")
            country = median_listing_price_df[median_listing_price_df["RegionType"] == "country"]
            country_dates = country[date_columns].reset_index()
            country_dates["StateName"] = "United States"
            country = country_dates.melt(
                id_vars=["StateName"], var_name="Date", value_name="Value"
            )

            res = pd.concat([states, country])

            res = res[res["Date"] != "index"]

            df = res[res["StateName"] == input.state()]

            last_value = df.iloc[-1,-1]
            second_last_value = df.iloc[-2,-1]

            percentage_change = ((last_value - second_last_value)/second_last_value *100)
            sign = "+" if percentage_change > 0 else "-"
            return f"{sign}{percentage_change:.2f}%"
        
with ui.layout_column_wrap():
    with ui.value_box(showcase=icon_svg("dollar-sign")):
        "Current Median List Price (City)"

        @render.ui
        def price2():
            date_columns = median_listing_price_df.columns[6:]

            # Filter by state and get available cities
            df_state = median_listing_price_df[median_listing_price_df["StateName"] == input.state()]
            
            if df_state.empty:
                return "No data available"

            # Filter by city
            df_city = df_state[df_state["RegionName"] == input.city()]
            if df_city.empty:
                return "No data available"

            # Process data
            df_city = df_city.melt(id_vars=["RegionName"], var_name="Date", value_name="Value")
            df_city = df_city[df_city["Date"] != "index"]

            last_value = df_city.iloc[-1, -1]  # Get most recent price
            return f"${last_value:,.0f}"
    
        
    
        # ---- DYNAMIC CITY DROPDOWN ----
        @render.ui
        def update_city_choices():
            selected_state = input.state()
            available_cities = median_listing_price_df.loc[
                median_listing_price_df["StateName"] == selected_state, "RegionName"
            ].unique()
            return ui.update_select("city", choices=sorted(available_cities)) 
        
    with ui.value_box(showcase=icon_svg("house")):
            "Home Inventory % Change (City)"  # Updated title to reflect city-level data
            @render.ui
            def change2():
                date_columns = median_listing_price_df.columns[6:]

                # Filter by state first (optional, to narrow down the dataset)
                df_state = median_listing_price_df[median_listing_price_df["StateName"] == input.state()]
                
                if df_state.empty:
                    return "No data available for this state"

                # Filter by city (RegionName)
                df_city = df_state[df_state["RegionName"] == input.city()]
                
                if df_city.empty:
                    return "No data available for this city"

                # Melt the dataframe to get Date and Value columns
                df_melted = df_city.melt(id_vars=["RegionName"], var_name="Date", value_name="Value")
                df_melted = df_melted[df_melted["Date"] != "index"]

                if len(df_melted) < 2:
                    return "Not enough data for comparison"

                # Get the last and second-to-last values
                last_value = df_melted.iloc[-1, -1]  # Last value
                second_last_value = df_melted.iloc[-2, -1]  # Second-to-last value

                # Calculate percentage change
                percentage_change = ((last_value - second_last_value) / second_last_value) * 100
                sign = "+" if percentage_change > 0 else "-"
                return f"{sign}{abs(percentage_change):.2f}%"


# Plotly visualization of Median Home Price Per State

with ui.navset_card_underline(title = "Median List Price      (For Best Results Filter on RegionName and StateName)"):

    with ui.nav_panel("Plot", icon = icon_svg("chart-line")):

        @render_plotly
        def list_price_plot():
            # Grouping by State Name and specifying the Date Columns
            price_grouped = median_listing_price_df.groupby('StateName').mean(numeric_only=True)     
            date_columns = median_listing_price_df.columns[6:]
            price_grouped_dates = price_grouped[date_columns].reset_index()   
            price_df_for_viz = price_grouped_dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")

            price_df_for_viz = filter_by_date(price_df_for_viz, input.date_range())

            if input.state() == "United States":
                df = price_df_for_viz
            else:
                df = price_df_for_viz[price_df_for_viz["StateName"] == input.state()]


            # Creating Visualization using Ployly
            fig = px.line(df, x="Date", y="Value", color="StateName")
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            return fig
    with ui.nav_panel("Table", icon=icon_svg("table")):
        @render.data_frame
        def list_price_data():
            if input.state() == "United States":
                df = median_listing_price_df
            else:
                df = median_listing_price_df[median_listing_price_df["StateName"] == input.state()]
            
            # ✅ Correct way to freeze columns in Shiny for Python
            return render.DataGrid(df, filters=True)  # Freezes first column

# Plotly visualization of Homes For Sale Per State
with ui.navset_card_underline(title = "Home Inventory     (For Best Results Filter on RegionName and StateName)"):

    with ui.nav_panel("Plot", icon = icon_svg("chart-line")):

        @render_plotly
        def for_sale_plot():
            # Grouping by State Name and specifying the Date Columns
            for_sale_grouped = for_sale_inventory_df.groupby('StateName').sum(numeric_only=True)
            date_columns = for_sale_inventory_df.columns[6:]
            for_sale_grouped_grouped_dates = for_sale_grouped[date_columns].reset_index()
            for_sale_df_for_viz = for_sale_grouped_grouped_dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")


            for_sale_df_for_viz = filter_by_date(for_sale_df_for_viz, input.date_range())

            if input.state() == "United States":
                df = for_sale_df_for_viz
            else:
                df = for_sale_df_for_viz[for_sale_df_for_viz["StateName"] == input.state()]

            # Creating Visualization using Plotly
            fig = px.line(df, x="Date", y="Value", color="StateName")
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            return fig
        
    with ui.nav_panel("Table", icon = icon_svg("table")):
        @render.data_frame
        def for_sale_data():
            if input.state() == "United States":
                df = for_sale_inventory_df
            else:
                df = for_sale_inventory_df[for_sale_inventory_df["StateName"] == input.state()]
            
            # ✅ Correct way to freeze columns in Shiny for Python
            return render.DataGrid(df, filters=True)  # Freezes first column
            
            '''
            if input.state() == "United States":
                df = for_sale_inventory_df
            else:
                df = for_sale_inventory_df[for_sale_inventory_df["StateName"] == input.state()]
            return output_data_frame(df, options={"frozen_columns": ["StateName"]})
            '''

# Plotly visualization of Listings Per State
with ui.navset_card_underline(title = "New Listings     (For Best Results Filter on RegionName and StateName)"):

    with ui.nav_panel("Plot", icon = icon_svg("chart-line")):

        @render_plotly
        def listings_plot():
            # Grouping by State Name and specifying the Date Columns
            new_listings_grouped = new_listings_df.groupby('StateName').sum(numeric_only=True)
            date_columns = new_listings_df.columns[6:]
            new_listings_grouped_dates = new_listings_grouped[date_columns].reset_index()
            new_listings_df_for_viz = new_listings_grouped_dates.melt(id_vars=["StateName"], var_name="Date", value_name="Value")
                    
            new_listings_df_for_viz = filter_by_date(new_listings_df_for_viz, input.date_range())
            
            
            if input.state() == "United States":
                df = new_listings_df_for_viz
            else:
                df = new_listings_df_for_viz[new_listings_df_for_viz["StateName"] == input.state()]


            # Creating Visualization using Ployly
            fig = px.line(df, x="Date", y="Value", color="StateName")
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            return fig

    with ui.nav_panel("Table", icon = icon_svg("table")):
        @render.data_frame
        def listings_data():
            if input.state() == "United States":
                df = new_listings_df
            else:
                df = new_listings_df[new_listings_df["StateName"] == input.state()]
            
            # ✅ Correct way to freeze columns in Shiny for Python
            return render.DataGrid(df, filters=True)  # Freezes first column    
                