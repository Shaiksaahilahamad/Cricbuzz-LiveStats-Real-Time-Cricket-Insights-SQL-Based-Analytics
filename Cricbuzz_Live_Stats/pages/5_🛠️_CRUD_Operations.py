# pages/5_🛠️_CRUD_Operations.py
import streamlit as st
from utils.db_connection import execute_query
from datetime import datetime, date

def main():
    st.header("🛠️ CRUD Operations")
    
    # Operation selection dropdown
    operation = st.selectbox(
        "Choose operation:",
        ["Create", "Read", "Update", "Delete"],
        key="crud_operation"
    )
    
    st.divider()
    
    if operation == "Create":
        create_player()
    elif operation == "Read":
        read_players()
    elif operation == "Update":
        update_player()
    elif operation == "Delete":
        delete_player()

def create_player():
    """Create a new player"""
    st.subheader("➕ Create New Player")
    
    # Use session state to persist form data and success message
    if 'create_success' not in st.session_state:
        st.session_state.create_success = None
    
    # Display success message if it exists
    if st.session_state.create_success:
        st.success(st.session_state.create_success)
        if st.button("Create Another Player"):
            st.session_state.create_success = None
            st.rerun()
        return
    
    with st.form("create_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*", placeholder="Virat Kohli")
            country = st.text_input("Country*", placeholder="India")
            role = st.selectbox(
                "Playing Role*",
                ["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Captain"]
            )
        
        with col2:
            batting_style = st.text_input("Batting Style", placeholder="Right-handed")
            bowling_style = st.text_input("Bowling Style", placeholder="Right-arm medium")
            
            min_date = date(1950, 1, 1)
            max_date = date.today()
            default_date = date(1990, 1, 1)
            
            date_of_birth = st.date_input(
                "Date of Birth", 
                value=default_date,
                min_value=min_date,
                max_value=max_date
            )
        
        submitted = st.form_submit_button("📝 Create Player")
        
        if submitted:
            if not name or not country or not role:
                st.warning("⚠️ Please fill in all required fields.")
                return

            query = """
                INSERT INTO crud_info 
                (name, country, role, batting_style, bowling_style, date_of_birth)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (name.strip(), country.strip(), role, batting_style.strip(), bowling_style.strip(), date_of_birth)

            result = execute_query(query, values, fetch=False)

            if result:
                st.session_state.create_success = f"✅ Player **{name}** is created successfully!"
                st.rerun()
            else:
                st.error("❌ Error creating player. Please try again.")

def read_players():
    """Read and display players"""
    st.subheader("📖 View Players")
    
    # Search input
    search_term = st.text_input("🔍 Search by Name", placeholder="Enter player name")
    
    # View button
    if st.button("👁️ View All Players", type="primary"):
        if search_term:
            query = """
                SELECT *, ROW_NUMBER() OVER (ORDER BY id) as sno 
                FROM crud_info 
                WHERE name ILIKE %s 
                ORDER BY id
            """
            params = (f"%{search_term.strip()}%",)
        else:
            query = """
                SELECT *, ROW_NUMBER() OVER (ORDER BY id) as sno 
                FROM crud_info 
                ORDER BY id
            """
            params = ()

        players = execute_query(query, params)

        if players:
            # Format player data
            display_data = [
                {
                    "SNo": player['sno'],
                    "ID": player['id'],
                    "Name": player['name'],
                    "Country": player['country'],
                    "Role": player['role'],
                    "Batting Style": player['batting_style'],
                    "Bowling Style": player['bowling_style'],
                    "Date of Birth": player['date_of_birth'],
                    "Created At": player['created_at']
                }
                for player in players
            ]

            st.success(f"✅ Found {len(players)} player(s).")
            st.dataframe(display_data, use_container_width=True)
        else:
            st.warning("⚠️ No players found with the given name.")

def update_player():
    """Update a player"""
    st.subheader("✏️ Update Player")
    
    # Use session state to persist success message
    if 'update_success' not in st.session_state:
        st.session_state.update_success = None
    
    # Display success message if it exists
    if st.session_state.update_success:
        st.success(st.session_state.update_success)
        if st.button("Update Another Player"):
            st.session_state.update_success = None
            st.rerun()
        return
    
    # Fetch players (latest first)
    players = execute_query("SELECT * FROM crud_info ORDER BY id DESC")

    if not players:
        st.warning("⚠️ No players available to update.")
        return

    # Dropdown mapping
    player_options = {
        f"{p['name']} ({p['country']}) - ID: {p['id']}": p['id']
        for p in players
    }

    selected_option = st.selectbox("Select a player to update:", list(player_options.keys()))

    if selected_option:
        player_id = player_options[selected_option]
        current = next((p for p in players if p['id'] == player_id), None)

        if current:
            with st.form("update_form"):
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input("Full Name*", value=current['name'])
                    new_country = st.text_input("Country*", value=current['country'])
                    new_role = st.selectbox(
                        "Playing Role*",
                        ["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Captain"],
                        index=["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Captain"].index(
                            current['role']) if current['role'] in 
                            ["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Captain"] else 0
                    )

                with col2:
                    new_batting = st.text_input("Batting Style", value=current.get('batting_style', ''))
                    new_bowling = st.text_input("Bowling Style", value=current.get('bowling_style', ''))

                    # Handle date parsing
                    min_date = date(1950, 1, 1)
                    max_date = date.today()

                    raw_dob = current.get('date_of_birth')
                    try:
                        current_dob = datetime.strptime(str(raw_dob), '%Y-%m-%d').date()
                    except Exception:
                        current_dob = date(1990, 1, 1)

                    new_dob = st.date_input(
                        "Date of Birth",
                        value=current_dob,
                        min_value=min_date,
                        max_value=max_date
                    )

                submitted = st.form_submit_button("Update Player")

                if submitted:
                    if new_name and new_country and new_role:
                        query = """
                            UPDATE crud_info 
                            SET name = %s, country = %s, role = %s, 
                                batting_style = %s, bowling_style = %s, date_of_birth = %s
                            WHERE id = %s
                        """
                        result = execute_query(
                            query, 
                            (new_name, new_country, new_role, new_batting, new_bowling, new_dob, player_id),
                            fetch=False
                        )

                        if result:
                            st.session_state.update_success = f"✅ Player **{new_name}** is updated successfully!"
                            st.rerun()
                        else:
                            st.error("❌ Failed to update player.")
                    else:
                        st.warning("⚠️ Please fill in all required fields.")

def delete_player():
    """Delete a player"""
    st.subheader("🗑️ Delete Player")

    # Use session state to persist success message
    if 'delete_success' not in st.session_state:
        st.session_state.delete_success = None
    
    # Display success message if it exists
    if st.session_state.delete_success:
        st.success(st.session_state.delete_success)
        if st.button("Delete Another Player"):
            st.session_state.delete_success = None
            st.rerun()
        return
    
    # Fetch all players
    players = execute_query("SELECT * FROM crud_info ORDER BY id DESC")

    if not players:
        st.warning("⚠️ No players available to delete.")
        return

    # Dropdown options with name + ID
    player_options = {
        f"{p['name']} ({p['country']}) - ID: {p['id']}": p['id']
        for p in players
    }

    selected = st.selectbox("Select a player to delete:", list(player_options.keys()))

    if selected:
        player_id = player_options[selected]
        player = next((p for p in players if p['id'] == player_id), None)

        if player:
            st.write("### 📋 Player Details:")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**ID:** {player['id']}")
                st.write(f"**Name:** {player['name']}")
                st.write(f"**Country:** {player['country']}")
                st.write(f"**Role:** {player['role']}")

            with col2:
                st.write(f"**Batting Style:** {player.get('batting_style', 'N/A')}")
                st.write(f"**Bowling Style:** {player.get('bowling_style', 'N/A')}")
                st.write(f"**Date of Birth:** {player.get('date_of_birth', 'N/A')}")

            # Warning and confirmation
            st.error("🚨 This action is permanent and cannot be undone.")
            st.markdown(f"🔒 To confirm, type the player name: **`{player['name']}`**")

            user_input = st.text_input("Confirm by typing the player name exactly:")

            if user_input == player['name']:
                if st.button("🗑️ Confirm Delete", type="secondary"):
                    query = "DELETE FROM crud_info WHERE id = %s"
                    result = execute_query(query, (player_id,), fetch=False)

                    if result:
                        st.session_state.delete_success = f"✅ Player **{player['name']}** is deleted successfully!"
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete player.")
            elif user_input:
                st.warning("⚠️ Player name does not match. Please type the name exactly to confirm.")

if __name__ == "__main__":
    main()