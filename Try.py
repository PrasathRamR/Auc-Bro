# Imports
import streamlit as st
import pandas as pd
from streamlit_card import card
import hmac

st.set_page_config(
    page_title="Auc-Bro",  # Title of the app
    page_icon="auc-removebg-preview.png",  
    layout="wide",  # Layout of the app ("centered" or "wide")
    initial_sidebar_state="expanded"  # Sidebar state ("expanded" or "collapsed")
)

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

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
st.write("For registrations, please contact")
st.button("Contact Us", on_click="mailto:rpstram@gmail.com")

if not check_password():
    st.stop()


# Function: Load the data into a DataFrame
def load_data(file, file_type):
    if file_type == "CSV":
        return pd.read_csv(file)
    elif file_type == "XLSX":
        return pd.read_excel(file)
    else:
        raise ValueError("Unsupported file type")

# StreamLit: Title
st.title("Auc-Bro: Auction Analysis Partner")
st.sidebar.image("auc.png",width=250)

# File type toggle
file_type_toggle = st.checkbox("Upload XLSX file (toggle off for CSV)", value=False)
file_type = "XLSX" if file_type_toggle else "CSV"

# File uploader
file_extension = "xlsx" if file_type == "XLSX" else "csv"
auction_list_file = st.file_uploader(f"Upload a {file_type} file", type=[file_extension])

# Initialize session state for the four Playing XI teams if not already done
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

if auction_list_file is not None:
    try:
        auction_list = load_data(auction_list_file, file_type)

        # Ensure required columns exist
        if "First Name" not in auction_list.columns or "Surname" not in auction_list.columns:
            st.error("The file must have 'First Name' and 'Surname' columns.")
        else:
            # Sidebar Filters
            with st.sidebar:
                st.header("Filter Options")

                # First Filter
                filter_column_1 = st.selectbox("Select the first column to filter", auction_list.columns, key="filter1")
                unique_values_1 = auction_list[filter_column_1].dropna().unique()
                selected_value_1 = st.selectbox(f"Select value for '{filter_column_1}'", unique_values_1, key="value1")

                # Second Filter
                filter_column_2 = st.selectbox("Select the second column to filter", auction_list.columns, key="filter2")
                unique_values_2 = auction_list[filter_column_2].dropna().unique()
                selected_value_2 = st.selectbox(f"Select value for '{filter_column_2}'", unique_values_2, key="value2")

                # Third Filter
                filter_column_3 = st.selectbox("Select the third column to filter", auction_list.columns, key="filter3")
                unique_values_3 = auction_list[filter_column_3].dropna().unique()
                selected_value_3 = st.selectbox(f"Select value for '{filter_column_3}'", unique_values_3, key="value3")

            # Apply Filters Sequentially
            filtered_data = auction_list[
                (auction_list[filter_column_1] == selected_value_1) &
                (auction_list[filter_column_2] == selected_value_2) &
                (auction_list[filter_column_3] == selected_value_3)
            ]

            # Concatenate "First Name" and "Surname"
            concatenated_names = filtered_data.apply(
                lambda row: f"{row['First Name']} {row['Surname']}", axis=1
            ).tolist()

            # Display the concatenated names in a selectbox
            with st.sidebar:
                st.write("Filtered Names:")
                if concatenated_names:
                    selected_name = st.selectbox("Select a player from the filtered results:", concatenated_names)

                    # Select which team to add the player to
                    team_choice = st.selectbox(
                        "Select the team to add the player:",
                        ["First Playing XI", "Second Playing XI", "Third Playing XI", "Fourth Playing XI"]
                    )

                    # Confirm button
                    if st.button("Confirm"):
                        # Add the player to the selected team if not already present
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
                    st.write("No results match the selected filters.")

            # Display the Playing XI Teams in Cards with individual flush buttons
            st.write("### Teams")

                # Use st.columns to create a two-column layout
            col1, col2 = st.columns(2)

                # First Playing XI Card in the first column
            with col1:
                card(
                    title="",
                    text="\n".join(st.session_state["first_playing_xi"]["Player Name"].tolist()) or "No players added",
                    key="card1"
                )
                if st.button("Flush First Playing XI"):
                    flush_team("first_playing_xi")
                    st.success("First Playing XI has been cleared!")

                # Second Playing XI Card in the second column
            with col2:
                card(
                    title="",
                    text="\n".join(st.session_state["second_playing_xi"]["Player Name"].tolist()) or "No players added",
                    key="card2"
                )
                if st.button("Flush Second Playing XI"):
                    flush_team("second_playing_xi")
                    st.success("Second Playing XI has been cleared!")

                # Third Playing XI Card in the first column (below First Playing XI)
            with col1:
                card(
                title="",
                text="\n".join(st.session_state["third_playing_xi"]["Player Name"].tolist()) or "No players added",                    key="card3"
                )
                if st.button("Flush Third Playing XI"):
                    flush_team("third_playing_xi")
                    st.success("Third Playing XI has been cleared!")

                # Fourth Playing XI Card in the second column (below Second Playing XI)
            with col2:
                card(
                    title="",
                    text="\n".join(st.session_state["fourth_playing_xi"]["Player Name"].tolist()) or "No players added",
                    key="card4"
                )
                if st.button("Flush Fourth Playing XI"):
                    flush_team("fourth_playing_xi")
                    st.success("Fourth Playing XI has been cleared!")
    except Exception as e:
        st.error(f"Error loading file: {e}")
