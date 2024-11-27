import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import json
import hmac
import openpyxl

st.set_page_config(
    page_title="Auc-Biddy",  # Title of the app
    page_icon="auc.png",  
    layout="wide",  # Layout of the app ("centered" or "wide")
    initial_sidebar_state="expanded"  # Sidebar state ("expanded" or "collapsed")
)

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        st.title("Auc-Buddy: Your Auction Companion")
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)
        st.write("For registrations, please mailto: rpstram@gmail.com / praveenram.ramasubramani@gmail.com")

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
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


if "auction_list_file_df" not in st.session_state:
    st.session_state["auction_list_file_df"] = None

# Function: Load the data into a DataFrame
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

    with st.sidebar:
        st.image("auc.png", width=250)
        st.header("Filter Options")

        if st.session_state.get("auction_list_file_df") is not None:
            auction_list = st.session_state["auction_list_file_df"]
        
            
            # Dynamically create filters based on available columns
        num_filters = 4  # Number of filters to allow
        filters = {}

        if st.session_state.get("auction_list_file_df") is not None:
            filtered_data = auction_list  # Start with the full DataFrame
        
        if st.session_state.get("auction_list_file_df") is not None:
            st.success("Filters Activated")
            for i in range(num_filters):
                filter_column = st.selectbox(f"Select column for Filter {i + 1}", ["None"] + list(auction_list.columns), key=f"filter_col_{i}")
                if filter_column != "None":
                    unique_values = ["All"] + auction_list[filter_column].dropna().unique().tolist()
                    selected_value = st.selectbox(f"Select value for '{filter_column}'", unique_values, key=f"filter_val_{i}")
                    if selected_value != "All":
                        # Apply filter to the data
                        filtered_data = filtered_data[filtered_data[filter_column] == selected_value]
                        filters[filter_column] = selected_value
        else:
            st.warning("Please upload a file to view the Filters.")
    if st.session_state["auction_list_file_df"] is not None:
        st.data_editor(filtered_data)
    else:
        st.warning("Please upload a file to view the data.")
       


def my_teams():
    # Initialize session state for teams
    if "first_playing_xi" not in st.session_state:
        st.session_state["first_playing_xi"] = pd.DataFrame(columns=["Player Name"])
    if "second_playing_xi" not in st.session_state:
        st.session_state["second_playing_xi"] = pd.DataFrame(columns=["Player Name"])
    if "third_playing_xi" not in st.session_state:
        st.session_state["third_playing_xi"] = pd.DataFrame(columns=["Player Name"])
    if "fourth_playing_xi" not in st.session_state:
        st.session_state["fourth_playing_xi"] = pd.DataFrame(columns=["Player Name"])

    # Function to flush a specific Playing XI DataFrame
    def flush_team(team_name):
        st.session_state[team_name] = pd.DataFrame(columns=["Player Name"])
    
    # Check if auction_list_file_df exists in session state
    

        # Sidebar Filters
    with st.sidebar:
        st.image("auc.png", width=250)
        if st.session_state.get("auction_list_file_df") is not None:
            auction_list = st.session_state["auction_list_file_df"]
            st.header("Filter Options")
            
            # Dynamically create filters based on available columns
            num_filters = 4  # Number of filters to allow
            filters = {}
            filtered_data = auction_list  # Start with the full DataFrame
            
            for i in range(num_filters):
                filter_column = st.selectbox(f"Select column for Filter {i + 1}", ["None"] + list(auction_list.columns), key=f"filter_col_{i}")
                if filter_column != "None":
                    unique_values = ["All"] + auction_list[filter_column].dropna().unique().tolist()
                    selected_value = st.selectbox(f"Select value for '{filter_column}'", unique_values, key=f"filter_val_{i}")
                    if selected_value != "All":
                        # Apply filter to the data
                        filtered_data = filtered_data[filtered_data[filter_column] == selected_value]
                        filters[filter_column] = selected_value
            
            # If no filters applied, show a message
        
            
        

                # Concatenate "First Name" and "Surname" if available
            if "First Name" in filtered_data.columns and "Surname" in filtered_data.columns:
                filtered_data["Full Name"] = filtered_data["First Name"] + " " + filtered_data["Surname"]
                concatenated_names = filtered_data["Full Name"].tolist()

                st.write("Filtered Names:")
                if concatenated_names:
                    selected_name = st.selectbox("Select a player from the filtered results:", concatenated_names)

                    # Select team to add the player
                    team_choice = st.selectbox(
                        "Select the team to add the player:",
                        ["First Playing XI", "Second Playing XI", "Third Playing XI", "Fourth Playing XI"]
                    )

                    # Confirm button
                    if st.button("Confirm"):
                        if team_choice == "First Playing XI":
                            team_df = st.session_state["first_playing_xi"]
                        elif team_choice == "Second Playing XI":
                            team_df = st.session_state["second_playing_xi"]
                        elif team_choice == "Third Playing XI":
                            team_df = st.session_state["third_playing_xi"]
                        else:  # Fourth Playing XI
                            team_df = st.session_state["fourth_playing_xi"]

                        if selected_name not in team_df["Player Name"].values:
                            team_df.loc[len(team_df)] = [selected_name]
                            st.success(f"Player '{selected_name}' has been added to the {team_choice}!")
                        else:
                            st.warning(f"Player '{selected_name}' is already in the {team_choice}.")
                else:
                    st.write("No names available to select.")
            else:
                st.warning("Please upload a file with 'First Name' and 'Surname' columns to view the Filters.")
        else:
            st.warning("Please upload a file to view the Filters.")

        # Display the Playing XI Teams in Cards with individual flush buttons
    # Display the Playing XI Teams in Tabs
    st.write("### Teams")
    tabs = st.tabs(["First Playing XI", "Second Playing XI", "Third Playing XI", "Fourth Playing XI"])

    # First Playing XI Tab
    with tabs[0]:
        st.write("### First Playing XI")
        first_playing_xi = st.session_state["first_playing_xi"].copy()
        edited_first_playing_xi = st.data_editor(first_playing_xi, key="editor_first_playing_xi")
        if st.button("Flush First Playing XI", key="flush1"):
            flush_team("first_playing_xi")
            st.success("First Playing XI has been cleared!")
        else:
            # Update session state only if there are changes
            if not first_playing_xi.equals(edited_first_playing_xi):
                st.session_state["first_playing_xi"] = edited_first_playing_xi

    # Second Playing XI Tab
    with tabs[1]:
        st.write("### Second Playing XI")
        second_playing_xi = st.session_state["second_playing_xi"].copy()
        edited_second_playing_xi = st.data_editor(second_playing_xi, key="editor_second_playing_xi")
        if st.button("Flush Second Playing XI", key="flush2"):
            flush_team("second_playing_xi")
            st.success("Second Playing XI has been cleared!")
        else:
            if not second_playing_xi.equals(edited_second_playing_xi):
                st.session_state["second_playing_xi"] = edited_second_playing_xi

    # Third Playing XI Tab
    with tabs[2]:
        st.write("### Third Playing XI")
        third_playing_xi = st.session_state["third_playing_xi"].copy()
        edited_third_playing_xi = st.data_editor(third_playing_xi, key="editor_third_playing_xi")
        if st.button("Flush Third Playing XI", key="flush3"):
            flush_team("third_playing_xi")
            st.success("Third Playing XI has been cleared!")
        else:
            if not third_playing_xi.equals(edited_third_playing_xi):
                st.session_state["third_playing_xi"] = edited_third_playing_xi

    # Fourth Playing XI Tab
    with tabs[3]:
        st.write("### Fourth Playing XI")
        fourth_playing_xi = st.session_state["fourth_playing_xi"].copy()
        edited_fourth_playing_xi = st.data_editor(fourth_playing_xi, key="editor_fourth_playing_xi")
        if st.button("Flush Fourth Playing XI", key="flush4"):
            flush_team("fourth_playing_xi")
            st.success("Fourth Playing XI has been cleared!")
        else:
            if not fourth_playing_xi.equals(edited_fourth_playing_xi):
                st.session_state["fourth_playing_xi"] = edited_fourth_playing_xi
    
def squads():
    if st.session_state.get("team_list") is not None:
        st.title("Squads")
        with st.sidebar:
            st.image("auc.png", width=250)
    else:
        st.warning("Please set up teams in the Live Auction tab before viewing squads.")
        with st.sidebar:
            st.image("auc.png", width=250)
            

def live_auction():
    st.title("LIVE AUCTION")
    st.sidebar.image("auc.png", width=250)

    # Initialize session state for persistent data
    if "setup_complete" not in st.session_state:
        st.session_state.setup_complete = False
    if "team_list" not in st.session_state:
        st.session_state.team_list = []
    if "budgets" not in st.session_state:
        st.session_state.budgets = {}
    if "cumulative_deductions" not in st.session_state:
        st.session_state.cumulative_deductions = {}
    if "player_data" not in st.session_state:
        st.session_state.player_data = {team: [] for team in st.session_state.team_list}
    if "bidding_history" not in st.session_state:
        st.session_state.bidding_history = []
    if "auction_list_file_df" not in st.session_state:
        st.session_state.auction_list_file_df = None

    # Save auction data to JSON
    def save_auction_data():
        data = {
            "team_list": st.session_state.team_list,
            "budgets": st.session_state.budgets,
            "player_data": st.session_state.player_data,
        }
        
        return json.dumps(data)
        

    # Load auction data from JSON
    def load_auction_data(uploaded_file):
        data = json.load(uploaded_file)
        st.session_state.team_list = data.get("team_list", [])
        st.session_state.budgets = data.get("budgets", {})
        st.session_state.player_data = data.get("player_data", {})
        st.session_state.setup_complete = True
        st.success("Auction data loaded successfully!")

    if not st.session_state.setup_complete:
        total_budget = st.number_input("Enter the total Budget for each team (in Lakhs):", min_value=0, step=1, key="total_budget")
        num_teams = st.number_input("Enter the number of teams:", min_value=4, step=1, key="num_teams")

        team_inputs = []
        for team in range(num_teams):
            teamname = st.text_input(f"Enter the team name for team {team + 1}:", key=f'text_{team + 1}')
            team_inputs.append(teamname)

        if st.button("Save Teams"):
            if all(team_inputs):
                st.session_state.team_list = team_inputs
                st.session_state.budgets = {team: total_budget for team in team_inputs}
                st.session_state.cumulative_deductions = {team: 0 for team in team_inputs}
                st.session_state.player_data = {team: [] for team in team_inputs}
                st.session_state.setup_complete = True
            else:
                st.warning("Please fill in all team names before proceeding.")
    else:
        st.header("Auction Management")

        # Sidebar for Player Selection
        with st.sidebar:
            if st.session_state.auction_list_file_df is not None:
                st.write("### Select Player by Player ID")
                player_id = st.number_input("Enter Player ID:", min_value=1, step=1, key="player_id")
                sold_bool = st.radio("Is the player sold?", ['Sold', 'Unsold'])
                if sold_bool == 'Sold':
                    sell_value = st.number_input("Enter the price (in Lakhs): ", min_value=0, key="sell_val")
                    team_sold = st.selectbox("Sold to: ", st.session_state.team_list)
                    rtm_check = st.checkbox("RTM")
                    add_player_button = st.button("Add Player")
                else:
                    st.error("Player is unsold!!")

                if player_id <= len(st.session_state.auction_list_file_df):
                    global selected_player_row
                    selected_player_row = st.session_state.auction_list_file_df.iloc[player_id - 1]
                    selected_player = f"{selected_player_row['First Name']} {selected_player_row['Surname']}"

                    # Check if the player is already added
                    player_exists = any(
                        player["Player ID"] == player_id
                        for team in st.session_state.team_list
                        for player in st.session_state.player_data[team]
                    )

                    if sold_bool == "Sold":
                        if player_exists:
                            st.warning(f"Player {selected_player} is already assigned to a team. Cannot add again.")
                        elif add_player_button:
                            player_data = {
                                "Player ID": player_id,
                                "Name": selected_player,
                                "Price": sell_value,
                                "RTM": rtm_check
                            }
                            st.session_state.player_data[team_sold].append(player_data)
                            st.session_state.budgets[team_sold] -= sell_value  # Deduct budget for the sold team
                            st.success(f"Player {selected_player} added to team {team_sold}. Remaining Budget: {st.session_state.budgets[team_sold]} Lakhs.")
        #new_sel = st.session_state.auction_list_file_df.iloc[player_id - 1] 
        if st.session_state.auction_list_file_df is not None:
            st.data_editor(selected_player_row.to_frame().T)
        else:
            st.warning("Please upload a file to view the data.")
        # Display Teams and Players
        st.write("### Teams and Players")
        tabs = st.tabs(st.session_state.team_list)
        for i, tab in enumerate(tabs):
            with tab:
                team_name = st.session_state.team_list[i]
                st.code(f"Current Budget = {st.session_state.budgets[team_name]}")
                st.write(f"Managing {team_name}")
                
                team_players = st.session_state.player_data.get(team_name, [])
                if team_players:
                    # Display current team players in a table
                    team_df = pd.DataFrame(team_players)

                    # Allow removal of players
                    remove_player_id = st.number_input(f"Enter Player ID to remove from {team_name}:", min_value=0, step=1, key=f"remove_player_{team_name}")
                    remove_button = st.button(f"Remove Player from {team_name}", key=f"remove_button_{team_name}")

                    if remove_button:
                        player_to_remove = next((p for p in team_players if p["Player ID"] == remove_player_id), None)
                        if player_to_remove:
                            team_players.remove(player_to_remove)
                            st.session_state.budgets[team_name] += player_to_remove["Price"]  # Refund the price
                            st.success(f"Player {player_to_remove['Name']} removed from {team_name}. Remaining Budget: {st.session_state.budgets[team_name]} Lakhs.")
                        else:
                            st.warning(f"No player with ID {remove_player_id} found in {team_name}.")

                    # Display editable dataframe for team players
                    st.data_editor(pd.DataFrame(team_players), key=f"team_df_{team_name}")
                else:
                    st.write("No players added yet.")


        # Save Button
        st.download_button("Save Data", save_auction_data(), file_name="auction_data.json", mime="application/json")

        # Upload File
        uploaded_file = st.file_uploader("Upload Auction Data", type=["json"])
        if uploaded_file is not None:
            load_auction_data(uploaded_file)

def retention():
    # Initialize session state for retention
    if "number_of_retained_players" not in st.session_state:
        st.session_state.number_of_retained_players = 0
    if "retained_players" not in st.session_state:
        st.session_state.retained_players = []
    if "retained_players_df" not in st.session_state:
        st.session_state.retained_players_df = pd.DataFrame(columns=["Player Name", "Price (in Lakhs)"])

    if st.session_state.get("team_list") is not None:
        st.title("Retention")

        team_list = st.session_state["team_list"]

        # Select team to enter retained players
        team_name = st.selectbox("Select team to enter the retained players:", team_list)

        # Input the number of retained players
        num_retained_players = st.number_input(
            "Enter the number of retained players:",
            min_value=0,
            step=1,
            key="num_retained_players",
        )

        retained_players = []
        for i in range(num_retained_players):
            # Input retained player details
            player_name = st.text_input(
                f"Enter the name of retained player {i + 1}:",
                key=f"retained_player_name_{i}",
            )
            player_price = st.number_input(
                f"Enter the price of retained player {i + 1} (in Lakhs):",
                min_value=0,
                step=1,
                key=f"retained_player_price_{i}",
            )
            retained_players.append((player_name, player_price))

        # Update retained players DataFrame
        st.session_state.retained_players_df = pd.DataFrame(
            retained_players, columns=["Player Name", "Price (in Lakhs)"]
        )

        

        st.success(
            f"Retained players for {team_name} have been entered. Remaining Budget: {st.session_state.budgets[team_name]} Lakhs."
        )

        # Display retained players for the selected team
        st.write("### Retained Players")
        st.data_editor(st.session_state.retained_players_df)

        # Push to Squads
        if st.button("Push to Squads"):
            for player_name, player_price in retained_players:
                player_data = {
                    "Player ID": None,  # Since this is a retained player, no ID is needed
                    "Name": player_name,
                    "Price": player_price,
                    "RTM": False,  # Retention doesn't use RTM
                }
                st.session_state.player_data[team_name].append(player_data)
                st.session_state.budgets[team_name]-=player_price

            st.success(f"Retained players have been added to {team_name}'s squad.")
            st.session_state.retained_players = []  # Clear retained players for the next input

        with st.sidebar:
            st.image("auc.png", width=250)
    else:
        st.warning("Please set up teams in the Live Auction tab before viewing retention.")
        with st.sidebar:
            st.image("auc.png", width=250)






selected = option_menu(
        menu_title=None,
        options=["Home", "My Teams","Auction", "Retention"],
        icons=["house","card-list","people","hammer", "file-arrow-down"],
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



