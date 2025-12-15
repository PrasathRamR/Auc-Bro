import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import json
import hmac
import openpyxl # Used for reading XLSX files

st.set_page_config(
    page_title="Auc-Biddy",  # Title of the app
    page_icon="auc.png",  
    layout="wide",  # Layout of the app ("centered" or "wide")
    initial_sidebar_state="expanded"  # Sidebar state ("expanded" or "collapsed")
)

# --- Global Session State Initialization (CRITICAL for Streamlit stability) ---

# DataFrames and Data
if "auction_list_file_df" not in st.session_state:
    st.session_state["auction_list_file_df"] = None

# Live Auction Setup
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "team_list" not in st.session_state:
    st.session_state.team_list = []
if "budgets" not in st.session_state:
    st.session_state.budgets = {}
if "total_budget" not in st.session_state:
    st.session_state.total_budget = 0 # To store the initial budget for reset/retention
if "player_data" not in st.session_state:
    st.session_state.player_data = {}

# Retention Data
if "retention_data" not in st.session_state:
    st.session_state.retention_data = {} # {team_name: [(name, price), ...]}

# My Teams DataFrames
if "first_playing_xi" not in st.session_state:
    st.session_state["first_playing_xi"] = pd.DataFrame(columns=["Player Name"])
if "second_playing_xi" not in st.session_state:
    st.session_state["second_playing_xi"] = pd.DataFrame(columns=["Player Name"])
if "third_playing_xi" not in st.session_state:
    st.session_state["third_playing_xi"] = pd.DataFrame(columns=["Player Name"])
if "fourth_playing_xi" not in st.session_state:
    st.session_state["fourth_playing_xi"] = pd.DataFrame(columns=["Player Name"])


def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        st.image("auc.png", width=250)
        st.title("Auc-Buddy: Your Auction Companion")
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)
        st.write("For registrations, please mailto: rpstram@gmail.com / praveenram.ramasubramani@gmail.com")

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets.get(
            "passwords", {}
        ) and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

if not check_password():
    st.stop()


# Function: Load the data into a DataFrame (Only kept for reference, not used by home_page)
def load_data(file, file_type):
    if file_type == "CSV":
        return pd.read_csv(file)
    elif file_type == "XLSX":
        return pd.read_excel(file)
    else:
        raise ValueError("Unsupported file type")

def home_page():    
    file_type_toggle = st.toggle("Upload CSV file", value=False, label_visibility='hidden')
    file_type = "XLSX" if file_type_toggle else "CSV"
    
    if file_type == 'XLSX':
        st.info("You should upload a XLSX file, to upload a CSV file use the toggle above")
    else:
        st.info("You should upload a CSV file, to upload a XLSX file use the toggle above")

    # File uploader
    file_extension = "xlsx" if file_type == "XLSX" else "csv"
    auction_list_file = st.file_uploader(f"Upload a {file_type} file", type=[file_extension])
    
    if auction_list_file is not None:
        if file_extension == 'csv':
            auc_file_read = pd.read_csv(auction_list_file)
        elif file_extension == 'xlsx':
            auc_file_read = pd.read_excel(auction_list_file)
            
        st.session_state["auction_list_file_df"] = pd.DataFrame(auc_file_read)
        st.success("File uploaded successfully!")
        
    filtered_data = pd.DataFrame() # Initialize empty DataFrame outside the block

    with st.sidebar:
        st.image("auc.png", width=250)
        st.header("Filter Options")

        if st.session_state.get("auction_list_file_df") is not None:
            st.success("Filters Activated")
            auction_list = st.session_state["auction_list_file_df"]
            filtered_data = auction_list.copy() # CRITICAL: Start with a copy of the full DataFrame
            num_filters = 4
            filters = {}

            for i in range(num_filters):
                filter_column = st.selectbox(f"Select column for Filter {i + 1}", ["None"] + list(auction_list.columns), key=f"filter_col_home_{i}")
                
                if filter_column != "None":
                    # Convert to string for safe unique list creation and selection
                    unique_values = ["All"] + auction_list[filter_column].dropna().astype(str).unique().tolist()
                    selected_value = st.selectbox(f"Select value for '{filter_column}'", unique_values, key=f"filter_val_home_{i}")
                    
                    if selected_value != "All":
                        # Apply filter to the data, ensuring types match for comparison
                        filtered_data = filtered_data[filtered_data[filter_column].astype(str) == selected_value]
                        filters[filter_column] = selected_value
        else:
            st.warning("Please upload a file to view the Filters.")
    
    # Display the data outside the sidebar
    if st.session_state["auction_list_file_df"] is not None:
        if not filtered_data.empty:
            st.subheader(f"Filtered Data ({len(filtered_data)} rows)")
            st.data_editor(filtered_data, key="home_data_editor")
        else:
            st.warning("No data matches the selected filters.")
    else:
        st.warning("Please upload a file to view the data.")


def my_teams():
    
    # Function to flush a specific Playing XI DataFrame
    def flush_team(team_name):
        st.session_state[team_name] = pd.DataFrame(columns=["Player Name"])
    
    # Initialize filtered_data outside the conditional block
    filtered_data = pd.DataFrame()
    auction_list = None

    # --- Sidebar Filters and Player Selection ---
    with st.sidebar:
        st.image("auc.png", width=250)
        
        if st.session_state.get("auction_list_file_df") is not None:
            auction_list = st.session_state["auction_list_file_df"]
            st.header("Filter Options")
            
            # CRITICAL: Start with a copy of the full DataFrame for filtering
            filtered_data = auction_list.copy() 
            num_filters = 4
            
            for i in range(num_filters):
                filter_column = st.selectbox(f"Select column for Filter {i + 1}", ["None"] + list(auction_list.columns), key=f"filter_col_team_{i}")
                
                if filter_column != "None":
                    unique_values = ["All"] + auction_list[filter_column].dropna().astype(str).unique().tolist()
                    selected_value = st.selectbox(f"Select value for '{filter_column}'", unique_values, key=f"filter_val_team_{i}")
                    
                    if selected_value != "All":
                        # Apply filter to the data
                        filtered_data = filtered_data[filtered_data[filter_column].astype(str) == selected_value]
            
            # Player Selection Widget
            if "First Name" in filtered_data.columns and "Surname" in filtered_data.columns and not filtered_data.empty:
                # CRITICAL FIX: Ensure 'Full Name' is calculated on the filtered data
                filtered_data["Full Name"] = filtered_data["First Name"].astype(str) + " " + filtered_data["Surname"].astype(str)
                concatenated_names = filtered_data["Full Name"].tolist()

                st.write("Filtered Names:")
                selected_name = st.selectbox("Select a player from the filtered results:", concatenated_names)

                # Select team to add the player
                team_choice = st.selectbox(
                    "Select the team to add the player:",
                    ["First Playing XI", "Second Playing XI", "Third Playing XI", "Fourth Playing XI"]
                )
                
                team_key_map = {
                    "First Playing XI": "first_playing_xi",
                    "Second Playing XI": "second_playing_xi",
                    "Third Playing XI": "third_playing_xi",
                    "Fourth Playing XI": "fourth_playing_xi"
                }
                current_team_key = team_key_map[team_choice]

                # Confirm button
                if st.button("Add Player to Team"):
                    team_df = st.session_state[current_team_key]
                    new_row = {"Player Name": selected_name}

                    if selected_name not in team_df["Player Name"].values:
                        # CRITICAL FIX: Use pd.concat for adding a row (safer than .loc with len)
                        st.session_state[current_team_key] = pd.concat([team_df, pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"Player '{selected_name}' has been added to the {team_choice}!")
                    else:
                        st.warning(f"Player '{selected_name}' is already in the {team_choice}.")
            elif auction_list is not None and not filtered_data.empty:
                st.warning("Data is filtered, but 'First Name' and 'Surname' columns are missing for player selection.")
            else:
                 st.warning("Please upload a file to view the Filters.")
        else:
            st.warning("Please upload a file to view the Filters.")

    # --- Main Display and Edit Logic ---
    st.write("### Playing XI Teams")
    team_keys = ["first_playing_xi", "second_playing_xi", "third_playing_xi", "fourth_playing_xi"]
    tab_names = ["First Playing XI", "Second Playing XI", "Third Playing XI", "Fourth Playing XI"]
    tabs = st.tabs(tab_names)

    for i, tab in enumerate(tabs):
        team_key = team_keys[i]
        team_name = tab_names[i]
        
        with tab:
            st.write(f"### {team_name}")
            
            # Display and allow editing
            current_df = st.session_state[team_key].copy()
            edited_df = st.data_editor(current_df, key=f"editor_{team_key}", num_rows="dynamic")
            
            # Handle state update from data editor
            if not current_df.equals(edited_df):
                 st.session_state[team_key] = edited_df

            # Handle flush button
            if st.button(f"Flush {team_name}", key=f"flush_{team_key}"):
                flush_team(team_key) 
                st.success(f"{team_name} has been cleared!")
                st.rerun() # Recommended to immediately show the cleared state


def squads():
    if not st.session_state.team_list:
        st.warning("Please set up teams in the Auction tab before viewing squads.")
    else:
        st.title("Squads")
        st.write("View the current budgets and players bought/retained for each team.")
        
        # Display Teams and Players using tabs
        tabs = st.tabs(st.session_state.team_list)
        for i, team_name in enumerate(st.session_state.team_list):
            with tabs[i]:
                st.code(f"Current Budget = {st.session_state.budgets.get(team_name, 'N/A')} Lakhs")
                st.write(f"### {team_name} Squad")
                
                team_players = st.session_state.player_data.get(team_name, [])
                if team_players:
                    team_df = pd.DataFrame(team_players)
                    st.data_editor(team_df, key=f"squad_df_{team_name}")
                else:
                    st.info("No players added or retained yet.")
                    
    with st.sidebar:
        st.image("auc.png", width=250)


def live_auction():
    st.title("LIVE AUCTION")
    
    # Save auction data to JSON
    def save_auction_data():
        data = {
            "team_list": st.session_state.team_list,
            "budgets": st.session_state.budgets,
            "player_data": st.session_state.player_data,
            "total_budget": st.session_state.total_budget, # Save the initial budget
        }
        return json.dumps(data)
        
    # Load auction data from JSON
    def load_auction_data(uploaded_file):
        data = json.load(uploaded_file)
        st.session_state.team_list = data.get("team_list", [])
        st.session_state.budgets = data.get("budgets", {})
        st.session_state.player_data = data.get("player_data", {})
        st.session_state.total_budget = data.get("total_budget", 0)
        st.session_state.setup_complete = True
        st.success("Auction data loaded successfully! Reloading...")
        st.rerun() # Rerun to apply new state

    if not st.session_state.setup_complete:
        
        # Store total_budget in session state so it can be used for budget reset in retention
        st.session_state.total_budget = st.number_input("Enter the total Budget for each team (in Lakhs):", min_value=0, step=1, key="total_budget_input")
        num_teams = st.number_input("Enter the number of teams:", min_value=1, step=1, key="num_teams")

        team_inputs = []
        for team in range(num_teams):
            teamname = st.text_input(f"Enter the team name for team {team + 1}:", key=f'text_{team + 1}')
            team_inputs.append(teamname)

        if st.button("Save Teams"):
            if all(team_inputs) and st.session_state.total_budget > 0:
                st.session_state.team_list = team_inputs
                # CRITICAL: Initialize based on the input total_budget_input
                st.session_state.budgets = {team: st.session_state.total_budget for team in team_inputs} 
                st.session_state.player_data = {team: [] for team in team_inputs}
                st.session_state.setup_complete = True
                st.success("Teams saved successfully! Restarting the page to apply setup.")
                st.rerun()
            elif st.session_state.total_budget == 0:
                 st.warning("Total budget must be greater than 0.")
            else:
                st.warning("Please fill in all team names before proceeding.")
    else:
        st.header("Auction Management")

        # Sidebar for Player Selection
        with st.sidebar:
            st.image("auc.png", width=250)
            
            if st.session_state.auction_list_file_df is not None:
                st.write("### Select Player by Player ID")
                max_id = len(st.session_state.auction_list_file_df)
                player_id = st.number_input("Enter Player ID (Index starts at 1):", min_value=1, max_value=max_id, step=1, key="player_id")
                
                # Player Info Preview
                selected_player_row = pd.Series()
                selected_player = "N/A"
                if 1 <= player_id <= max_id:
                    selected_player_row = st.session_state.auction_list_file_df.iloc[player_id - 1]
                    try:
                        selected_player = f"{selected_player_row.get('First Name', '')} {selected_player_row.get('Surname', '')}".strip()
                    except AttributeError:
                         selected_player = f"Player {player_id}"

                st.markdown(f"**Player Name:** {selected_player}")

                sold_bool = st.radio("Is the player sold?", ['Sold', 'Unsold'])
                
                sell_value = 0
                team_sold = None
                rtm_check = False
                add_player_button = False

                if sold_bool == 'Sold':
                    sell_value = st.number_input("Enter the price (in Lakhs): ", min_value=0, key="sell_val")
                    team_sold = st.selectbox("Sold to: ", st.session_state.team_list)
                    rtm_check = st.checkbox("RTM (Right to Match)")
                    add_player_button = st.button("Add Player to Squad")
                else:
                    st.error("Player is unsold!!")

                # Logic to Add Player
                if 1 <= player_id <= max_id:
                    
                    # Check if the player is already added
                    player_exists = any(
                        player["Player ID"] == player_id
                        for team in st.session_state.team_list
                        for player in st.session_state.player_data.get(team, [])
                    )

                    if sold_bool == "Sold" and add_player_button:
                        if player_exists:
                            st.warning(f"Player {selected_player} is already assigned to a team. Cannot add again.")
                        elif sell_value > st.session_state.budgets.get(team_sold, 0):
                             st.error(f"Cannot buy! {team_sold} only has {st.session_state.budgets.get(team_sold, 0)} Lakhs remaining.")
                        else:
                            player_data = {
                                "Player ID": player_id,
                                "Name": selected_player,
                                "Price": sell_value,
                                "RTM": rtm_check
                            }
                            st.session_state.player_data[team_sold].append(player_data)
                            st.session_state.budgets[team_sold] -= sell_value  # Deduct budget
                            st.success(f"Player {selected_player} added to team {team_sold}. Remaining Budget: {st.session_state.budgets[team_sold]} Lakhs.")
                            st.rerun()
                
            else:
                st.warning("Please upload a file to view player data.")

        # Main Area: Player Row Display
        if not selected_player_row.empty:
            st.write("### Player Details")
            st.data_editor(selected_player_row.to_frame().T, key="selected_player_view")
        
        # Main Area: Display Teams and Players (Same logic as in original)
        st.write("### Teams and Players")
        tabs = st.tabs(st.session_state.team_list)
        for i, tab in enumerate(tabs):
            with tab:
                team_name = st.session_state.team_list[i]
                current_budget = st.session_state.budgets.get(team_name, 'N/A')
                st.code(f"Current Budget = {current_budget} Lakhs")
                st.write(f"Managing {team_name}")
                
                team_players = st.session_state.player_data.get(team_name, [])
                
                if team_players:
                    team_df = pd.DataFrame(team_players)

                    # Display editable dataframe for team players
                    st.write("Current Roster (Read-only, use inputs below to remove):")
                    st.data_editor(team_df, key=f"team_df_{team_name}", disabled=True)
                    
                    # Allow removal of players
                    remove_player_id = st.number_input(f"Enter Player ID to remove from {team_name}:", min_value=0, step=1, key=f"remove_player_{team_name}")
                    remove_button = st.button(f"Remove Player from {team_name}", key=f"remove_button_{team_name}")

                    if remove_button and remove_player_id > 0:
                        player_to_remove = next((p for p in team_players if p["Player ID"] == remove_player_id), None)
                        
                        if player_to_remove:
                            st.session_state.player_data[team_name].remove(player_to_remove)
                            st.session_state.budgets[team_name] += player_to_remove["Price"]  # Refund the price
                            st.success(f"Player {player_to_remove['Name']} removed from {team_name}. Remaining Budget: {st.session_state.budgets[team_name]} Lakhs.")
                            st.rerun()
                        else:
                            st.warning(f"No player with ID {remove_player_id} found in {team_name}.")

                else:
                    st.write("No players added yet.")


        # Save/Load Functionality
        col1, col2 = st.columns(2)
        with col1:
             st.download_button("Save Auction Data", save_auction_data(), file_name="auction_data.json", mime="application/json")
        with col2:
             uploaded_file = st.file_uploader("Load Auction Data", type=["json"])
             if uploaded_file is not None:
                 load_auction_data(uploaded_file)


def retention():
    if not st.session_state.team_list:
        st.warning("Please set up teams in the Auction tab before managing retention.")
    else:
        st.title("Retention")
        
        team_list = st.session_state["team_list"]
        team_name = st.selectbox("Select team to enter the retained players:", team_list, key="retention_team_select")

        # Load existing retained players for the selected team from the dedicated state
        current_retained = st.session_state.retention_data.get(team_name, [])
        
        num_retained_players = st.number_input(
            f"Enter the number of retained players for {team_name}:",
            min_value=0,
            step=1,
            key=f"num_retained_players_{team_name}", 
            value=len(current_retained) 
        )

        retained_players_inputs = []
        for i in range(num_retained_players):
            # Try to pre-fill from current data
            default_name = current_retained[i][0] if i < len(current_retained) else ""
            default_price = current_retained[i][1] if i < len(current_retained) else 0

            player_name = st.text_input(
                f"Enter the name of retained player {i + 1}:",
                key=f"retained_player_name_{team_name}_{i}",
                value=default_name
            )
            player_price = st.number_input(
                f"Enter the price of retained player {i + 1} (in Lakhs):",
                min_value=0,
                step=1,
                key=f"retained_player_price_{team_name}_{i}",
                value=default_price
            )
            retained_players_inputs.append((player_name, player_price))
            
        # Store the current state of inputs
        st.session_state.retention_data[team_name] = retained_players_inputs
        
        # Display retained players for the selected team (using current inputs)
        retained_df = pd.DataFrame(retained_players_inputs, columns=["Player Name", "Price (in Lakhs)"])
        st.write("### Retained Players (Preview)")
        st.data_editor(retained_df, key=f"retention_preview_{team_name}", disabled=["Player Name", "Price (in Lakhs)"])
        
        # Push to Squads button and logic
        if st.button(f"Push {team_name} Retained Players to Squads and Deduct Budget"):
            
            # CRITICAL FIX: To correctly calculate budget, reset to total budget first 
            # (Assuming retention is done before buying in the Live Auction tab)
            st.session_state.budgets[team_name] = st.session_state.total_budget
            st.session_state.player_data[team_name] = [] # Clear previous list before appending

            for player_name, player_price in retained_players_inputs:
                player_data = {
                    "Player ID": None,
                    "Name": player_name,
                    "Price": player_price,
                    "RTM": False,
                }
                # Append the player data
                st.session_state.player_data[team_name].append(player_data)
                
                # Deduct budget
                st.session_state.budgets[team_name] -= player_price

            st.success(f"Retained players for {team_name} have been added to the squad. Remaining Budget: {st.session_state.budgets[team_name]} Lakhs.")
            st.rerun() # Rerun to update the budget display in the Auction tab

    with st.sidebar:
        st.image("auc.png", width=250)


# --- Main Menu and Page Routing ---
selected = option_menu(
    menu_title=None,
    options=["Home", "My Teams", "Auction", "Retention", "Squads"],
    icons=["house", "person-bounding-box", "hammer", "clipboard-data", "people"],
    default_index=0,
    orientation="horizontal",
)

if selected == "Home":
    st.title("Auc-Biddy: Your Auction Companion.")
    home_page()
elif selected == "My Teams":
    my_teams()
elif selected == "Auction":
    live_auction()
elif selected == "Retention":
    retention()
elif selected == "Squads":
    squads()
