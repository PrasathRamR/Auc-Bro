import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import json
import hmac
import openpyxl 
import random 

st.set_page_config(
    page_title="Auc-Biddy: IPL Auction 2026",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global Session State Initialization ---

if "auction_list_file_df" not in st.session_state:
    st.session_state["auction_list_file_df"] = None
if "unsold_players" not in st.session_state:
    # Stores Player IDs (1-based) of players who went unsold
    st.session_state["unsold_players"] = [] 

# Live Auction Setup
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "team_list" not in st.session_state:
    st.session_state.team_list = []
if "budgets" not in st.session_state:
    st.session_state.budgets = {}
if "total_budget" not in st.session_state:
    # Used to reset budget for retention, must be initialized
    st.session_state.total_budget = 0 
if "player_data" not in st.session_state:
    # {team_name: [{"Player ID": 1, "Name": "X", "Price": 200, "RTM": False}, ...]}
    st.session_state.player_data = {}
if "current_player_id" not in st.session_state:
    # Player ID (1-based index) currently being auctioned
    st.session_state.current_player_id = None 

# Retention Data (Used to manage retained players separate from auction buys)
if "retention_data" not in st.session_state:
    st.session_state.retention_data = {} 

# My Teams DataFrames (Optional, removed for brevity, keeping only key)
if "playing_xi_initialized" not in st.session_state:
    st.session_state["first_playing_xi"] = pd.DataFrame(columns=["Player Name"])
    # Add other playing_xi dataframes if needed in "My Teams" page


def check_password():
    """Simulates password check based on st.secrets."""
    # (Leaving your existing check_password implementation here)
    def login_form():
        st.image("auc.png", width=250)
        st.title("Auc-Buddy: Your Auction Companion")
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)
        st.write("For registrations, please mailto: rpstram@gmail.com / praveenram.ramasubramani@gmail.com")

    def password_entered():
        if st.session_state["username"] in st.secrets.get(
            "passwords", {}
        ) and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

if not check_password():
    st.stop()


def home_page():    
    # ... (File upload and filtering logic remains the same)
    file_type_toggle = st.toggle("Upload CSV file", value=False, label_visibility='hidden')
    file_type = "XLSX" if file_type_toggle else "CSV"
    
    st.info(f"You should upload a {file_type} file. Toggle above to switch file types.")

    file_extension = "xlsx" if file_type == "XLSX" else "csv"
    auction_list_file = st.file_uploader(f"Upload a {file_type} file", type=[file_extension])
    
    if auction_list_file is not None:
        try:
            if file_extension == 'csv':
                auc_file_read = pd.read_csv(auction_list_file)
            elif file_extension == 'xlsx':
                auc_file_read = pd.read_excel(auction_list_file)
            
            # --- CRITICAL FIX: Clean up column names after loading ---
            # Replaces spaces with underscores and removes special characters
            auc_file_read.columns = auc_file_read.columns.str.strip().str.replace('[^A-Za-z0-9_]+', '', regex=True).str.replace(' ', '_')
            
            # Add a List_Sr_No column if it doesn't exist (useful for indexing)
            if 'List_Sr_No' not in auc_file_read.columns:
                 auc_file_read.insert(0, 'List_Sr_No', range(1, 1 + len(auc_file_read)))
                 
            st.session_state["auction_list_file_df"] = pd.DataFrame(auc_file_read)
            st.session_state.current_player_id = 1 # Start auction player pool at ID 1
            st.success("File uploaded and player pool initialized!")
        except Exception as e:
            st.error(f"Error reading file. Please ensure the format is correct: {e}")
            st.session_state["auction_list_file_df"] = None
        
    filtered_data = pd.DataFrame() # Initialize outside the block

    with st.sidebar:
        st.image("auc.png", width=250)
        st.header("Filter Options")

        # Filtering logic... (kept simplified for focus on auction)
        if st.session_state.get("auction_list_file_df") is not None:
            st.success("Filters Activated")
            auction_list = st.session_state["auction_list_file_df"]
            filtered_data = auction_list.copy()
            valid_cols = [col for col in auction_list.columns if col not in ['First_Name', 'Surname']]

            # ... (rest of filtering UI) ...
        
    if st.session_state["auction_list_file_df"] is not None:
        # ... (display filtered data) ...
        pass


# Function to find the next player ID available for auction
def get_next_available_player_id(current_id):
    df = st.session_state.auction_list_file_df
    all_ids = set(df['List_Sr_No'].unique())
    
    # Get IDs of players already sold
    sold_ids = {p['Player ID'] for team in st.session_state.team_list for p in st.session_state.player_data.get(team, []) if p['Player ID'] is not None}
    
    # Include currently unsold players to be re-auctioned later
    remaining_pool = sorted(list(all_ids - sold_ids))
    
    # If the current player is unsold, keep them in the unsold list for the accelerated round.
    if current_id in st.session_state.unsold_players:
         # Prioritize the next player in the main list, leaving the unsold players for the end.
         next_main_player = min([id for id in remaining_pool if id > current_id], default=None)
         if next_main_player is not None:
             return next_main_player
         
         # If main list is exhausted, fetch from the stored unsold list
         remaining_unsold = sorted([id for id in st.session_state.unsold_players if id > current_id])
         if remaining_unsold:
              return remaining_unsold[0] # Next unsold player
         
         # Loop to the start of the remaining unsold pool if all IDs higher than current_id have been processed
         if st.session_state.unsold_players:
             return st.session_state.unsold_players[0] # Loop back to the first unsold player

    # Standard next player logic
    next_id = min([id for id in remaining_pool if id > current_id], default=None)

    if next_id is None and st.session_state.unsold_players:
        # Main list exhausted, start accelerated round with stored unsold players
        return st.session_state.unsold_players[0]
        
    return next_id


def set_next_player(player_id=None):
    if player_id is not None:
        st.session_state.current_player_id = player_id
    elif st.session_state.auction_list_file_df is not None:
        if st.session_state.current_player_id is None:
            # Start at ID 1 if not started
            st.session_state.current_player_id = 1 
        else:
            # Get the next player based on the available pool
            next_id = get_next_available_player_id(st.session_state.current_player_id)
            if next_id is None:
                st.warning("Auction Complete: No more players left in the pool.")
            st.session_state.current_player_id = next_id
    
    st.rerun() # Force rerun to update the auction floor


def live_auction():
    st.title("LIVE AUCTION 🔨")
    
    # Save/Load functions (kept the same)
    def save_auction_data():
        data = {
            "team_list": st.session_state.team_list,
            "budgets": st.session_state.budgets,
            "player_data": st.session_state.player_data,
            "total_budget": st.session_state.total_budget, 
            "unsold_players": st.session_state.unsold_players,
        }
        return json.dumps(data)
        
    def load_auction_data(uploaded_file):
        data = json.load(uploaded_file)
        st.session_state.team_list = data.get("team_list", [])
        st.session_state.budgets = data.get("budgets", {})
        st.session_state.player_data = data.get("player_data", {})
        st.session_state.total_budget = data.get("total_budget", 0)
        st.session_state.unsold_players = data.get("unsold_players", [])
        st.session_state.current_player_id = data.get("current_player_id", None)
        st.session_state.setup_complete = True
        st.success("Auction data loaded successfully! Reloading...")
        st.rerun() 

    if not st.session_state.setup_complete:
        st.header("1. Setup Teams and Budget")
        st.session_state.total_budget = st.number_input("Enter the total Budget for each team (in Lakhs):", min_value=0, step=1, key="total_budget_input")
        num_teams = st.number_input("Enter the number of teams:", min_value=1, step=1, key="num_teams")

        team_inputs = [st.text_input(f"Enter the team name for team {t + 1}:", key=f'text_{t + 1}') for t in range(num_teams)]

        if st.button("Save Teams"):
            if all(team_inputs) and st.session_state.total_budget > 0:
                st.session_state.team_list = team_inputs
                st.session_state.budgets = {team: st.session_state.total_budget for team in team_inputs}  
                st.session_state.player_data = {team: [] for team in team_inputs}
                st.session_state.setup_complete = True
                st.success("Teams saved! Now proceed to the auction floor.")
                st.rerun()
            elif st.session_state.total_budget == 0:
                 st.warning("Total budget must be greater than 0.")
            else:
                st.warning("Please fill in all team names before proceeding.")
    else:
        # --- Main Auction Interface ---
        
        # Sidebar Controls
        with st.sidebar:
            st.image("auc.png", width=250)
            st.subheader("Auction Controls")
            
            if st.session_state.auction_list_file_df is not None:
                if st.button("Next Player (Sequential)"):
                    set_next_player()
                
                manual_id = st.number_input("Or Enter Player ID Manually (Starts at 1):", 
                                            min_value=1, 
                                            max_value=len(st.session_state.auction_list_file_df) if st.session_state.auction_list_file_df is not None else 1, 
                                            step=1, 
                                            key="manual_player_id")
                if st.button("Load Specific Player"):
                    set_next_player(manual_id)
            else:
                st.warning("Upload list in Home tab first.")
            
            st.divider()
            
            # Budget Display in Sidebar 
            st.subheader("Team Budgets (Lakhs)")
            budget_df = pd.DataFrame(st.session_state.budgets.items(), columns=["Team", "Budget"])
            st.dataframe(budget_df, hide_index=True)


        # Auction Floor Display Logic
        if st.session_state.current_player_id is not None and st.session_state.auction_list_file_df is not None:
            
            player_id = st.session_state.current_player_id
            df = st.session_state.auction_list_file_df
            
            try:
                player_row = df[df['List_Sr_No'] == player_id].iloc[0]
                player_name = f"{player_row.get('First_Name', '')} {player_row.get('Surname', '')}".strip()
                
                # Use Reserve_Price_Rs_Lakh as the reserve price, handling potential NaN/string issues
                reserve_price_raw = player_row.get('Reserve_Price_Rs_Lakh', 0)
                try:
                    reserve_price = int(reserve_price_raw)
                except (ValueError, TypeError):
                    reserve_price = 0
                
                st.markdown(f"## 💥 Bidding On: **{player_name}** (ID: {player_id})")
                st.info(f"Reserve Price: **{reserve_price} Lakhs**")
                
                # Display Player Details
                with st.expander(f"Player Analysis: {player_name}"):
                    # Filter for display columns
                    display_cols = ['Country', 'Specialism', 'Test_caps', 'ODI_caps', 'T20_caps', 'IPL_2025_Team']
                    st.dataframe(player_row[display_cols].to_frame().T, hide_index=True)
                    
                st.divider()
                
                # --- Auction Result Form ---
                with st.form("Auction_Result_Form"):
                    col_status, col_price = st.columns(2)
                    
                    with col_status:
                        sold_or_unsold = st.radio("Auction Outcome:", ['Sold', 'Unsold'], key="auction_outcome")
                    
                    final_price = reserve_price 
                    rtm_applied_team = None

                    if sold_or_unsold == 'Sold':
                        with col_price:
                            final_price = st.number_input("Final Bid Price (Lakhs):", min_value=reserve_price, step=1, key="final_price_input")
                        
                        team_sold = st.selectbox("Winning Team:", st.session_state.team_list, key="winning_team")
                        
                        # RTM Logic
                        rtm_teams = [t for t in st.session_state.team_list if t != team_sold]
                        
                        if rtm_teams:
                            st.subheader("Right To Match (RTM) Option")
                            use_rtm = st.checkbox(f"Use RTM card?", key="rtm_used")
                            
                            if use_rtm:
                                rtm_applied_team = st.selectbox("Team that used RTM:", rtm_teams, key="rtm_team")

                    submitted = st.form_submit_button("Finalize and Move to Next Player")

                    if submitted:
                        if sold_or_unsold == 'Sold':
                            
                            buyer_team = rtm_applied_team if rtm_applied_team else team_sold
                            
                            if final_price > st.session_state.budgets.get(buyer_team, 0):
                                st.error(f"Transaction failed! **{buyer_team}** does not have enough budget ({st.session_state.budgets.get(buyer_team, 0)} Lakhs).")
                                # Do NOT move to next player
                            else:
                                player_data = {
                                    "Player ID": player_id,
                                    "Name": player_name,
                                    "Price": final_price,
                                    "RTM": bool(rtm_applied_team),
                                }
                                # Update squads and budget
                                st.session_state.player_data[buyer_team].append(player_data)
                                st.session_state.budgets[buyer_team] -= final_price
                                
                                # Remove from unsold list if present
                                if player_id in st.session_state.unsold_players:
                                    st.session_state.unsold_players.remove(player_id)
                                
                                st.success(f"Player **{player_name}** sold to **{buyer_team}** for **{final_price} Lakhs**.")
                                set_next_player() 

                        elif sold_or_unsold == 'Unsold':
                            if player_id not in st.session_state.unsold_players:
                                st.session_state.unsold_players.append(player_id)
                            st.warning(f"Player **{player_name}** is Unsold and added to the list for accelerated rounds.")
                            set_next_player()
                            
                        # st.rerun is inside set_next_player

            except Exception as e:
                st.error(f"Error processing player ID {player_id}. Check file data or skip player. Error: {e}")
                st.session_state.current_player_id = None
                st.rerun()

        elif st.session_state.auction_list_file_df is None:
            st.warning("Please upload the auction list file in the Home tab to begin the auction setup.")
        else:
            st.info("Setup complete. Click 'Next Player (Sequential)' in the sidebar to start the auction!")

        # Load/Save Functionality
        st.divider()
        st.subheader("Auction Data Management")
        col1, col2 = st.columns(2)
        with col1:
             st.download_button("Save Auction Data (JSON)", save_auction_data(), file_name="auction_data.json", mime="application/json")
        with col2:
             uploaded_file = st.file_uploader("Load Auction Data (JSON)", type=["json"])
             if uploaded_file is not None:
                 load_auction_data(uploaded_file)
        
        # Display Unsold List 
        if st.session_state.unsold_players:
             st.info(f"Unsold Players (IDs): {', '.join(map(str, sorted(st.session_state.unsold_players)))}")

def my_teams():
    # ... (Your existing My Teams logic here) ...
    st.title("My Playing XI Teams")
    st.info("This is where you arrange your purchased players into fantasy teams.")

def squads():
    if not st.session_state.team_list:
        st.warning("Please set up teams in the Auction tab before viewing squads.")
    else:
        st.title("Current Squads and Remaining Purse")
        st.write("View the complete roster and remaining budget for each team. ")
        
        tabs = st.tabs(st.session_state.team_list)
        for i, team_name in enumerate(st.session_state.team_list):
            with tabs[i]:
                current_budget = st.session_state.budgets.get(team_name, 'N/A')
                squad_count = len(st.session_state.player_data.get(team_name, []))
                
                col1, col2 = st.columns(2)
                with col1:
                     st.metric(label="Remaining Budget (Lakhs)", value=f"₹{current_budget:,}")
                with col2:
                     st.metric(label="Squad Count", value=f"{squad_count}")
                
                team_players = st.session_state.player_data.get(team_name, [])
                if team_players:
                    team_df = pd.DataFrame(team_players)
                    st.dataframe(team_df, hide_index=True)
                else:
                    st.info("No players added or retained yet.")
                    
    with st.sidebar:
        st.image("auc.png", width=250)


def retention():
    # ... (Your existing Retention logic here) ...
    st.title("Player Retention Management")
    st.info("Use this tab to pre-load players retained before the auction starts.")


# --- Main Menu and Page Routing ---
selected = option_menu(
    menu_title=None,
    options=["Home", "Auction", "Squads", "Retention", "My Teams"],
    icons=["house", "hammer", "people", "clipboard-data", "person-bounding-box"],
    default_index=1,
    orientation="horizontal",
)

if selected == "Home":
    st.title("Auc-Biddy: Auction List Management.")
    home_page()
elif selected == "Auction":
    live_auction()
elif selected == "Retention":
    retention()
elif selected == "Squads":
    squads()
elif selected == "My Teams":
    my_teams()
