import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import json


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
        st.warning("You should upload a XLSX file, to upload a CSV file use the toggle above")
    else:
        st.warning("You should upload a CSV file, to upload a XLSX file use the toggle above")

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
    if st.session_state["auction_list_file_df"] is not None:
            # Display the filtered DataFrame
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
    if st.session_state.get("auction_list_file_df") is not None:
        auction_list = st.session_state["auction_list_file_df"]

        # Sidebar Filters
        with st.sidebar:
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
    

    

def live_auction():
    # App title
    st.title("LIVE AUCTION")

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
        st.session_state.player_data = {}

    # Save data to JSON
    def save_data():
        data = {
            "team_list": st.session_state.team_list,
            "budgets": st.session_state.budgets,
            "cumulative_deductions": st.session_state.cumulative_deductions,
            "player_data": st.session_state.player_data,
        }
        return json.dumps(data)

    # Load data from JSON
    def load_data(uploaded_file):
        data = json.load(uploaded_file)
        st.session_state.team_list = data.get("team_list", [])
        st.session_state.budgets = data.get("budgets", {})
        st.session_state.cumulative_deductions = data.get("cumulative_deductions", {})
        st.session_state.player_data = data.get("player_data", {})
        st.session_state.setup_complete = True

    # Inputs section
    if not st.session_state.setup_complete:
        # Input fields for total budget and number of teams
        total_budget = st.number_input("Enter the total Budget for each team (in Cr / Million): ", min_value=0.00,step=0.25,format="%.2f" , key="total_budget")
        num_teams = st.number_input("Enter the number of teams: ", min_value=4, step=1, key="num_teams")

        # Input fields for team names
        team_inputs = []
        for team in range(num_teams):
            teamname = st.text_input(f"Enter the team name for team {team+1}: ", key=f'text_{team+1}')
            team_inputs.append(teamname)

        # Submit button to finalize inputs
        if st.button("Save Teams"):
            if all(team_inputs):  # Validate all team names are entered
                st.session_state.team_list = team_inputs
                st.session_state.budgets = {team: total_budget for team in team_inputs}
                st.session_state.cumulative_deductions = {team: 0 for team in team_inputs}
                st.session_state.player_data = {team: [] for team in team_inputs}
                st.session_state.setup_complete = True
            else:
                st.warning("Please fill in all team names before proceeding.")
    else:
        # Tabs for each team
        st.write("All inputs have been saved! Manage player retentions for each team below:")

        tabs = st.tabs(st.session_state.team_list)
        for i, tab in enumerate(tabs):
            with tab:
                team_name = st.session_state.team_list[i]
                st.write(f"Managing {team_name}")

                # Input for player's name and retention value
                player_name = st.text_input(f"Enter player name for {team_name}:", key=f"player_name_{team_name}")
                retention_value = st.number_input(
                    f"Enter retention value for {player_name} (in Cr / Million):",
                    min_value=0.00, step=0.25, format="%.2f",
                    key=f"retention_value_{team_name}",
                )

                # Add player to the team
                if st.button(f"Add Player to {team_name}", key=f"add_player_{team_name}"):
                    if player_name and retention_value > 0:
                        # Append player data and deduct budget
                        st.session_state.player_data[team_name].append({"name": player_name, "value": retention_value})
                        st.session_state.cumulative_deductions[team_name] += retention_value
                        st.session_state.budgets[team_name] -= retention_value
                        st.success(f"{player_name} added! Remaining budget for {team_name}: {st.session_state.budgets[team_name]} Cr/Million")
                    else:
                        st.warning("Please provide a valid player name and retention value.")

                # Display remaining budget and retained players
                st.write(f"Remaining Budget for {team_name}: {st.session_state.budgets[team_name]} Cr/Million")
                st.write("Retained Players:")
                for player in st.session_state.player_data[team_name]:
                    st.write(f"- {player['name']} ({player['value']} Cr/Million)")

    # Save and Load buttons
    st.download_button("Save Data", save_data(), file_name="auction_data.json", mime="application/json")

    uploaded_file = st.file_uploader("Load Data ", type="json")
    if uploaded_file is not None:
        load_data(uploaded_file)
        st.success("Data loaded successfully! Rerun the page from the menu at right top of the page to see updated UI.")
    with st.sidebar:
        st.image("auc.png",width=250)

def analysis_and_charts():
    with st.sidebar:
        st.image("auc.png",width=250)
        selected = option_menu(
            menu_title=None,
            options=["Analysis and Charts", "Settings"],
            icons=["clipboard-data","gear"],
            default_index=0,
            orientation="vertical",
        )
    if selected == "Analysis and Charts":
        st.title("Analysis and Charts")
    elif selected == "Settings":
        st.title("Settings")

st.set_page_config(
    page_title="Auc-Buddy",  # Title of the app
    page_icon="auc-removebg-preview.png",  
    layout="wide",  # Layout of the app ("centered" or "wide")
    initial_sidebar_state="expanded"  # Sidebar state ("expanded" or "collapsed")
)


selected = option_menu(
        menu_title=None,
        options=["Home", "My Teams", "Live Auction", "Analysis and Charts"],
        icons=["house","card-list","people","hammer","clipboard-data"],
        default_index=0,
        orientation="horizontal",

)

if selected == "Home":
    st.title("Auc-Buddy: Your Auction Companion.")
    home_page()
elif selected == "My Teams":
    my_teams()
elif selected == "Live Auction":
    live_auction()
elif selected == "Analysis and Charts":
    analysis_and_charts()



