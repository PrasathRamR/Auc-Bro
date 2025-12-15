import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import json
import hmac
import openpyxl # Used for reading XLSX files
import random # For simulating auction order or picking the next player

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
if "unsold_players" not in st.session_state:
    st.session_state["unsold_players"] = [] # To hold Player IDs of unsold players

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
if "current_player_id" not in st.session_state:
    st.session_state.current_player_id = None # Player currently being auctioned

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
        try:
            if file_extension == 'csv':
                auc_file_read = pd.read_csv(auction_list_file)
            elif file_extension == 'xlsx':
                auc_file_read = pd.read_excel(auction_list_file)
            
            # CRITICAL: Clean up column names by stripping whitespace and invalid characters
            auc_file_read.columns = auc_file_read.columns.str.strip().str.replace('[^A-Za-z0-9_ ]+', '', regex=True).str.replace(' ', '_')
            
            st.session_state["auction_list_file_df"] = pd.DataFrame(auc_file_read)
            st.success("File uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.session_state["auction_list_file_df"] = None
        
    filtered_data = pd.DataFrame() 

    with st.sidebar:
        st.image("auc.png", width=250)
        st.header("Filter Options")

        if st.session_state.get("auction_list_file_df") is not None:
            st.success("Filters Activated")
            auction_list = st.session_state["auction_list_file_df"]
            filtered_data = auction_list.copy() 
            num_filters = 4
            filters = {}
            
            # Get valid column names after cleanup
            valid_cols = [col for col in auction_list.columns if col not in ['First_Name', 'Surname']]

            for i in range(num_filters):
                filter_column = st.selectbox(f"Select column for Filter {i + 1}", ["None"] + valid_cols, key=f"filter_col_home_{i}")
                
                if filter_column != "None":
                    unique_values = ["All"] + auction_list[filter_column].dropna().astype(str).unique().tolist()
                    selected_value = st.selectbox(f"Select value for '{filter_column}'", unique_values, key=f"filter_val_home_{i}")
                    
                    if selected_value != "All":
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
    
    filtered_data = pd.DataFrame()
    auction_list = None

    # --- Sidebar Filters and Player Selection ---
    with st.sidebar:
        st.image("auc.png", width=250)
        
        if st.session_state.get("auction_list_file_df") is not None:
            auction_list = st.session_state["auction_list_file_df"]
            st.header("Filter Options")
            
            filtered_data = auction_list.copy() 
            num_filters = 4
            valid_cols = [col for col in auction_list.columns if col not in ['First_Name', 'Surname']]
            
            for i in range(num_filters):
                filter_column = st.selectbox(f"Select column for Filter {i + 1}", ["None"] + valid_cols, key=f"filter_col_team_{i}")
                
                if filter_column != "None":
                    unique_values = ["All"] + auction_list[filter_column].dropna().astype(str).unique().tolist()
                    selected_value = st.selectbox(f"Select value for '{filter_column}'", unique_values, key=f"filter_val_team_{i}")
                    
                    if selected_value != "All":
                        filtered_data = filtered_data[filtered_data[filter_column].astype(str) == selected_value]
            
            # Player Selection Widget
            if "First_Name" in filtered_data.columns and "Surname" in filtered_data.columns and not filtered_data.empty:
                
                filtered_data["Full Name"] = filtered_data["First_Name"].astype(str) + " " + filtered_data["Surname"].astype(str)
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
            
            current_df = st.session_state[team_key].copy()
            edited_df = st.data_editor(current_df, key=f"editor_{team_key}", num_rows="dynamic")
            
            if not current_df.equals(edited_df):
                 st.session_state[team_key] = edited_df

            if st.button(f"Flush {team_name}", key=f"flush_{team_key}"):
                flush_team(team_key)  
                st.success(f"{team_name} has been cleared!")
                st.rerun() 


def squads():
    if not st.session_state.team_list:
        st.warning("Please set up teams in the Auction tab before viewing squads.")
    else:
        st.title("Squads")
        st.write("View the current budgets and players bought/retained for each team.")
        
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
            "total_budget": st.session_state.total_budget, 
            "unsold_players": st.session_state.unsold_players,
        }
        return json.dumps(data)
        
    # Load auction data from JSON
    def load_auction_data(uploaded_file):
        data = json.load(uploaded_file)
        st.session_state.team_list = data.get("team_list", [])
        st.session_state.budgets = data.get("budgets", {})
        st.session_state.player_data = data.get("player_data", {})
        st.session_state.total_budget = data.get("total_budget", 0)
        st.session_state.unsold_players = data.get("unsold_players", [])
        st.session_state.setup_complete = True
        st.success("Auction data loaded successfully! Reloading...")
        st.rerun() 

    if not st.session_state.setup_complete:
        
        st.session_state.total_budget = st.number_input("Enter the total Budget for each team (in Lakhs):", min_value=0, step=1, key="total_budget_input")
        num_teams = st.number_input("Enter the number of teams:", min_value=1, step=1, key="num_teams")

        team_inputs = []
        for team in range(num_teams):
            teamname = st.text_input(f"Enter the team name for team {team + 1}:", key=f'text_{team + 1}')
            team_inputs.append(teamname)

        if st.button("Save Teams"):
            if all(team_inputs) and st.session_state.total_budget > 0:
                st.session_state.team_list = team_inputs
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
        st.header("Auction Floor")

        # --- Sidebar Controls ---
        with st.sidebar:
            st.image("auc.png", width=250)
            
            st.subheader("Auction Controls")
            
            # Function to select the next player
            def set_next_player(player_id=None):
                if player_id is None:
                    # Logic to select the next player ID sequentially or randomly
                    if st.session_state.auction_list_file_df is not None:
                        all_ids = set(st.session_state.auction_list_file_df.index.tolist())
                        
                        # Find already sold player IDs (index starts at 0, player_id starts at 1)
                        sold_ids = {p['Player ID'] - 1 for team in st.session_state.team_list for p in st.session_state.player_data.get(team, []) if p['Player ID'] is not None}
                        
                        # Add previously unsold players (if not already sold now)
                        unsold_ids = {pid - 1 for pid in st.session_state.unsold_players}

                        available_ids = sorted(list((all_ids - sold_ids) | unsold_ids))
                        
                        if available_ids:
                            # Pick the lowest available ID for a sequential feel
                            st.session_state.current_player_id = available_ids[0] + 1
                        else:
                            st.warning("Auction Complete: No more players left in the pool.")
                            st.session_state.current_player_id = None
                            return
                else:
                    st.session_state.current_player_id = player_id
                
                st.rerun()

            # Button to fetch the next player
            if st.session_state.auction_list_file_df is not None:
                if st.button("Next Player"):
                    set_next_player()
                
                # Manual Player ID Input (Useful for debugging or specific set calls)
                manual_id = st.number_input("Or Enter Player ID Manually (Starts at 1):", min_value=1, max_value=len(st.session_state.auction_list_file_df), step=1, key="manual_player_id")
                if st.button("Load Player"):
                    set_next_player(manual_id)
            else:
                st.warning("Please upload the auction file in the Home tab first.")
            
            st.divider()

            # Display Budgets
            st.subheader("Team Budgets (Lakhs)")
            budget_df = pd.DataFrame(st.session_state.budgets.items(), columns=["Team", "Budget"])
            st.dataframe(budget_df, hide_index=True)


        # --- Main Area: Auction Floor ---
        
        if st.session_state.current_player_id is not None and st.session_state.auction_list_file_df is not None:
            
            player_id = st.session_state.current_player_id
            df = st.session_state.auction_list_file_df
            
            try:
                # Player ID from session state is 1-based, index is 0-based
                player_row = df.iloc[player_id - 1] 
                
                player_name = f"{player_row.get('First_Name', '')} {player_row.get('Surname', '')}".strip()
                reserve_price = player_row.get('Reserve_Price_Rs_Lakh', 'N/A')

                st.markdown(f"## 🏏 Current Player: **{player_name}** (ID: {player_id})")
                st.info(f"Reserve Price: **{reserve_price} Lakhs**")
                
                # Display Player Details
                with st.expander("View Player Full Details"):
                    st.data_editor(player_row.to_frame().T, key="current_player_details")
                    
                st.divider()
                
                # --- Bidding and Result Form ---
                with st.form("Auction_Result_Form"):
                    col_sold, col_price = st.columns(2)
                    
                    with col_sold:
                        sold_or_unsold = st.radio("Auction Outcome:", ['Sold', 'Unsold'], key="auction_outcome")
                    
                    if sold_or_unsold == 'Sold':
                        with col_price:
                            final_price = st.number_input("Final Bid Price (Lakhs):", min_value=reserve_price if isinstance(reserve_price, (int, float)) else 0, step=1, key="final_price")
                        
                        team_sold = st.selectbox("Winning Team:", st.session_state.team_list, key="winning_team")
                        
                        # RTM Logic
                        st.subheader("Right To Match (RTM)")
                        # Identify teams eligible for RTM (usually teams that retained players, or specific rules)
                        # For simplicity, we assume RTM is available to all teams other than the buyer.
                        rtm_teams = [t for t in st.session_state.team_list if t != team_sold]
                        
                        use_rtm = st.checkbox(f"Was an RTM Card used by another team?", key="rtm_used")
                        
                        rtm_applied_team = None
                        if use_rtm:
                            rtm_applied_team = st.selectbox("Team that used RTM:", rtm_teams, key="rtm_team")
                        
                        st.markdown("**Note:** If RTM is used, the price and budget deduction apply to the RTM team, not the winning team.")


                    submitted = st.form_submit_button("Finalize Auction Result")

                    if submitted:
                        # Logic to finalize the auction
                        if sold_or_unsold == 'Sold':
                            
                            buyer_team = rtm_applied_team if use_rtm else team_sold
                            
                            if final_price > st.session_state.budgets.get(buyer_team, 0):
                                st.error(f"Transaction failed! {buyer_team} does not have enough budget ({st.session_state.budgets[buyer_team]} Lakhs).")
                            else:
                                player_data = {
                                    "Player ID": player_id,
                                    "Name": player_name,
                                    "Price": final_price,
                                    "RTM": use_rtm,
                                }
                                # Deduct budget and add to squad
                                st.session_state.player_data[buyer_team].append(player_data)
                                st.session_state.budgets[buyer_team] -= final_price
                                
                                # Remove player from the unsold list if they were there
                                if player_id in st.session_state.unsold_players:
                                    st.session_state.unsold_players.remove(player_id)
                                
                                st.success(f"Player **{player_name}** sold to **{buyer_team}** for **{final_price} Lakhs** (RTM: {'Yes' if use_rtm else 'No'}).")
                                
                                # Move to the next player
                                set_next_player() 

                        elif sold_or_unsold == 'Unsold':
                            st.session_state.unsold_players.append(player_id)
                            st.warning(f"Player **{player_name}** is Unsold.")
                            set_next_player()
                            
                        st.rerun()

            except IndexError:
                st.error(f"Error: Player ID {player_id} is out of bounds for the uploaded file.")
                st.session_state.current_player_id = None
                st.rerun()

        elif st.session_state.auction_list_file_df is None:
            st.warning("Please upload the auction list file in the Home tab to begin the auction setup.")
        else:
            st.info("Click 'Next Player' in the sidebar to start the auction!")

        # Display Live/Load Controls and Squads below the auction floor
        st.divider()
        st.subheader("Auction Data Management")
        col1, col2 = st.columns(2)
        with col1:
             st.download_button("Save Auction Data", save_auction_data(), file_name="auction_data.json", mime="application/json")
        with col2:
             uploaded_file = st.file_uploader("Load Auction Data", type=["json"])
             if uploaded_file is not None:
                 load_auction_data(uploaded_file)
        
        st.divider()
        st.subheader("Current Squads and Budget")
        squads_tabs = st.tabs(st.session_state.team_list)
        for i, team_name in enumerate(st.session_state.team_list):
            with squads_tabs[i]:
                current_budget = st.session_state.budgets.get(team_name, 'N/A')
                st.metric(label="Remaining Budget (Lakhs)", value=current_budget)
                
                team_players = st.session_state.player_data.get(team_name, [])
                if team_players:
                    st.dataframe(pd.DataFrame(team_players), hide_index=True)
                else:
                    st.write("No players yet.")


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
            
        st.session_state.retention_data[team_name] = retained_players_inputs
        
        retained_df = pd.DataFrame(retained_players_inputs, columns=["Player Name", "Price (in Lakhs)"])
        st.write("### Retained Players (Preview)")
        st.data_editor(retained_df, key=f"retention_preview_{team_name}", disabled=["Player Name", "Price (in Lakhs)"])
        
        if st.button(f"Push {team_name} Retained Players to Squads and Deduct Budget"):
            
            st.session_state.budgets[team_name] = st.session_state.total_budget
            st.session_state.player_data[team_name] = [] 

            for player_name, player_price in retained_players_inputs:
                player_data = {
                    "Player ID": None,
                    "Name": player_name,
                    "Price": player_price,
                    "RTM": False,
                }
                if not any(p['Name'] == player_name for p in st.session_state.player_data[team_name]):
                    st.session_state.player_data[team_name].append(player_data)
                
                st.session_state.budgets[team_name] -= player_price

            st.success(f"Retained players for {team_name} have been added to the squad. Remaining Budget: {st.session_state.budgets[team_name]} Lakhs.")
            st.rerun() 

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
