import streamlit as st
import random
import json
import os
import time
import hashlib

# Game variables - now using session state instead of globals
cardvalue = ["A", 2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K"]

# User profile system (same as original)
PROFILES_FILE = "blackjack_profiles.json"
TRANSACTIONS_FILE = "transactions.json"
ADMIN_PASSWORD = "blackjack2025"  # Change this to your preferred password

def hash_password(password):
    """Hash a password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_profiles(profiles):
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        try:
            with open(TRANSACTIONS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_transactions(transactions):
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f, indent=2)

def log_transaction(username, amount, payment_method, transaction_type="credit_purchase"):
    transactions = load_transactions()
    transaction = {
        "id": len(transactions) + 1,
        "username": username,
        "amount": amount,
        "payment_method": payment_method,
        "transaction_type": transaction_type,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "admin": st.session_state.get('admin_user', 'Unknown')
    }
    transactions.append(transaction)
    save_transactions(transactions)
    return transaction

def create_profile(username, password):
    return {
        "username": username,
        "password_hash": hash_password(password),  # Store hashed password
        "balance": 1000,
        "games_played": 0,
        "games_won": 0,
        "total_winnings": 0,
        "biggest_win": 0,
        "is_admin": False,  # Default to no admin privileges
        "created": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def init_session_state():
    """Initialize all session state variables"""
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'login_step' not in st.session_state:
        st.session_state.login_step = 'username'  # 'username' or 'password'
    if 'entered_username' not in st.session_state:
        st.session_state.entered_username = ""
    if 'game_phase' not in st.session_state:
        st.session_state.game_phase = 'login'  # login, betting, playing, game_over
    if 'player_hand' not in st.session_state:
        st.session_state.player_hand = []
    if 'bot_hand' not in st.session_state:
        st.session_state.bot_hand = []
    if 'shoe' not in st.session_state:
        st.session_state.shoe = []
    if 'total_bet' not in st.session_state:
        st.session_state.total_bet = 0
    if 'player_value' not in st.session_state:
        st.session_state.player_value = 0
    if 'dealer_value' not in st.session_state:
        st.session_state.dealer_value = 0
    if 'game_result' not in st.session_state:
        st.session_state.game_result = None
    if 'dealer_turn_complete' not in st.session_state:
        st.session_state.dealer_turn_complete = False
    if 'game_updated' not in st.session_state:
        st.session_state.game_updated = False
    if 'admin_mode' not in st.session_state:
        st.session_state.admin_mode = False
    if 'admin_user' not in st.session_state:
        st.session_state.admin_user = None

def init_shoe():
    """Initialize and shuffle the shoe"""
    st.session_state.shoe.clear()
    for _ in range(4):  # 4 decks
        for _ in range(4):  # 4 suits per deck
            for card in cardvalue:
                st.session_state.shoe.append(card)
    random.shuffle(st.session_state.shoe)

def calculate_hand_value(hand, is_dealer=False):
    """Calculate hand value with automatic Ace handling for dealer"""
    total = 0
    aces = 0
    
    for card in hand:
        if card in ["J", "Q", "K"]:
            total += 10
        elif card == "A":
            aces += 1
            total += 11  # Start with 11
        else:
            total += card
    
    # Adjust for Aces (convert 11s to 1s as needed)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    
    return total

def update_profile(result, bet_amount):
    """Update player profile with game results"""
    if not st.session_state.current_user:
        return
    
    # Prevent duplicate updates
    if hasattr(st.session_state, 'game_updated') and st.session_state.game_updated:
        return
        
    profiles = load_profiles()
    username = st.session_state.current_user['username']
    
    st.session_state.current_user['games_played'] += 1
    
    if result == "win":
        st.session_state.current_user['games_won'] += 1
        st.session_state.current_user['balance'] += bet_amount
        st.session_state.current_user['total_winnings'] += bet_amount
        if bet_amount > st.session_state.current_user['biggest_win']:
            st.session_state.current_user['biggest_win'] = bet_amount
    elif result == "lose":
        st.session_state.current_user['balance'] -= bet_amount
    
    profiles[username] = st.session_state.current_user
    save_profiles(profiles)
    
    # Mark this game as updated
    st.session_state.game_updated = True

def login_page():
    """Handle user login/registration with password protection"""
    st.title("🃏 Blackjack Login")
    
    profiles = load_profiles()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Login", "Register", "Leaderboard", "Admin/Cashier"])
    
    with tab1:
        st.subheader("Login to Existing Account")
        
        if st.session_state.login_step == 'username':
            # Step 1: Enter username
            username = st.text_input("Username:", key="login_username", value=st.session_state.entered_username)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Continue", key="username_continue"):
                    if username.strip():
                        if username in profiles:
                            st.session_state.entered_username = username
                            st.session_state.login_step = 'password'
                            st.rerun()
                        else:
                            st.error("Username not found!")
                    else:
                        st.error("Please enter a username!")
            
            with col2:
                if st.button("Back to Username", key="back_to_username", disabled=True):
                    pass  # This is disabled since we're already at username step
        
        elif st.session_state.login_step == 'password':
            # Step 2: Enter password
            st.info(f"Welcome back! Please enter your password for: **{st.session_state.entered_username}**")
            
            password = st.text_input("Password:", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login", key="password_login", type="primary"):
                    if password:
                        user_profile = profiles[st.session_state.entered_username]
                        if verify_password(password, user_profile['password_hash']):
                            st.session_state.current_user = user_profile
                            st.session_state.game_phase = 'betting'
                            st.session_state.login_step = 'username'  # Reset for next time
                            st.session_state.entered_username = ""
                            st.success(f"Welcome back, {st.session_state.entered_username}!")
                            st.rerun()
                        else:
                            st.error("Incorrect password!")
                    else:
                        st.error("Please enter your password!")
            
            with col2:
                if st.button("← Back to Username", key="back_to_username_from_password"):
                    st.session_state.login_step = 'username'
                    st.session_state.entered_username = ""
                    st.rerun()
    
    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Choose Username:", key="register_username")
        new_password = st.text_input("Choose Password:", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password:", type="password", key="confirm_password")
        
        if st.button("Create Account", key="register_btn"):
            if not new_username.strip():
                st.error("Username cannot be empty!")
            elif new_username in profiles:
                st.error("Username already exists!")
            elif len(new_password) < 4:
                st.error("Password must be at least 4 characters long!")
            elif new_password != confirm_password:
                st.error("Passwords don't match!")
            else:
                profiles[new_username] = create_profile(new_username, new_password)
                st.session_state.current_user = profiles[new_username]
                save_profiles(profiles)
                st.session_state.game_phase = 'betting'
                st.success(f"Account created! Welcome {new_username}!")
                st.rerun()
    
    with tab3:
        st.subheader("Leaderboard")
        if profiles:
            sorted_players = sorted(profiles.values(), key=lambda x: x['balance'], reverse=True)
            
            for i, player in enumerate(sorted_players[:10], 1):
                win_rate = (player['games_won']/max(1,player['games_played'])*100)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"{i}. {player['username']}")
                with col2:
                    st.write(f"${player['balance']}")
                with col3:
                    st.write(f"{player['games_played']} games")
                with col4:
                    st.write(f"{win_rate:.1f}% win rate")
        else:
            st.write("No players yet!")
    
    with tab4:
        admin_login_page()

def betting_page():
    """Handle betting phase"""
    st.title("🃏 Blackjack Game")
    
    # Display user info
    user = st.session_state.current_user
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Balance", f"${user['balance']}")
    with col2:
        st.metric("Games Played", user['games_played'])
    with col3:
        win_rate = (user['games_won']/max(1,user['games_played'])*100)
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    # Show admin badge if user is admin
    if user.get('is_admin', False):
        st.success("👑 Admin Account - You have administrative privileges")
    
    # Check if player is broke
    if user['balance'] <= 0:
        st.error("You're broke! Game over.")
        if st.button("Back to Login"):
            st.session_state.game_phase = 'login'
            st.rerun()
        return
    
    st.subheader("Place Your Bet")
    
    # Betting input
    bet_amount = st.number_input(
        f"Bet amount (Max: ${user['balance']}):",
        min_value=1,
        max_value=user['balance'],
        value=min(50, user['balance']),
        step=1
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Place Bet", type="primary"):
            st.session_state.total_bet = bet_amount
            # Initialize game
            if len(st.session_state.shoe) <= 52:
                init_shoe()
            
            # Deal initial cards
            st.session_state.player_hand = [st.session_state.shoe.pop(0), st.session_state.shoe.pop(0)]
            st.session_state.bot_hand = [st.session_state.shoe.pop(0), st.session_state.shoe.pop(0)]
            
            # Calculate initial values
            st.session_state.player_value = calculate_hand_value(st.session_state.player_hand)
            st.session_state.dealer_value = calculate_hand_value(st.session_state.bot_hand)
            
            st.session_state.game_phase = 'playing'
            st.session_state.dealer_turn_complete = False
            st.session_state.game_updated = False  # Reset for new game
            st.rerun()
    
    with col2:
        if st.button("Logout"):
            st.session_state.current_user = None
            st.session_state.game_phase = 'login'
            st.session_state.login_step = 'username'  # Reset login step
            st.session_state.entered_username = ""
            st.rerun()
    
    with col3:
        if st.button("View Stats"):
            show_stats()
    
    # Admin-only button
    with col4:
        if user.get('is_admin', False):
            if st.button("👑 Admin Panel", type="secondary"):
                st.session_state.game_phase = 'user_admin'
                st.rerun()

def playing_page():
    """Handle the main game playing phase"""
    st.title("🃏 Blackjack Game")
    
    # Display bet
    st.info(f"Current bet: ${st.session_state.total_bet}")
    
    # Display hands
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your Hand")
        hand_str = " | ".join([str(card) for card in st.session_state.player_hand])
        st.write(f"Cards: {hand_str}")
        st.write(f"**Value: {st.session_state.player_value}**")
        
        # Check for player bust or blackjack
        if st.session_state.player_value > 21:
            st.error("BUST! You went over 21!")
        elif st.session_state.player_value == 21:
            st.success("Blackjack! You got 21!")
    
    with col2:
        st.subheader("Dealer Hand")
        if st.session_state.dealer_turn_complete:
            # Show all dealer cards
            dealer_hand_str = " | ".join([str(card) for card in st.session_state.bot_hand])
            st.write(f"Cards: {dealer_hand_str}")
            st.write(f"**Value: {st.session_state.dealer_value}**")
            if st.session_state.dealer_value > 21:
                st.error("Dealer busts!")
        else:
            # Hide dealer's second card
            st.write(f"Cards: {st.session_state.bot_hand[0]} | ?")
            visible_value = calculate_hand_value([st.session_state.bot_hand[0]])
            st.write(f"Visible value: {visible_value}")
    
    # Game actions
    if st.session_state.player_value <= 21 and not st.session_state.dealer_turn_complete:
        st.subheader("Your Turn")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Hit", type="secondary"):
                # Draw a card
                new_card = st.session_state.shoe.pop(0)
                st.session_state.player_hand.append(new_card)
                st.session_state.player_value = calculate_hand_value(st.session_state.player_hand)
                st.rerun()
        
        with col2:
            if st.button("Stand", type="primary"):
                # Start dealer turn
                st.session_state.dealer_turn_complete = True
                dealer_play()
                st.rerun()
        
        with col3:
            if st.button("Double Down") and st.session_state.current_user['balance'] >= st.session_state.total_bet:
                # Double the bet and draw one card
                st.session_state.total_bet *= 2
                new_card = st.session_state.shoe.pop(0)
                st.session_state.player_hand.append(new_card)
                st.session_state.player_value = calculate_hand_value(st.session_state.player_hand)
                
                # Automatically stand after double down
                st.session_state.dealer_turn_complete = True
                dealer_play()
                st.rerun()
    
    # Handle game end
    if st.session_state.player_value > 21:
        # Player bust
        st.error(f"You lose ${st.session_state.total_bet}!")
        update_profile("lose", st.session_state.total_bet)
        st.session_state.game_result = "lose"
        show_game_end()
    elif st.session_state.dealer_turn_complete:
        determine_winner()

def dealer_play():
    """Handle dealer's automatic play"""
    st.session_state.dealer_value = calculate_hand_value(st.session_state.bot_hand)
    
    # Dealer hits until 17 or higher
    while st.session_state.dealer_value < 17:
        new_card = st.session_state.shoe.pop(0)
        st.session_state.bot_hand.append(new_card)
        st.session_state.dealer_value = calculate_hand_value(st.session_state.bot_hand)

def determine_winner():
    """Determine and display the winner"""
    player_val = st.session_state.player_value
    dealer_val = st.session_state.dealer_value
    
    st.subheader("Game Results")
    
    if dealer_val > 21:
        st.success(f"Dealer busts! You win ${st.session_state.total_bet}!")
        update_profile("win", st.session_state.total_bet)
        st.session_state.game_result = "win"
    elif player_val > dealer_val:
        st.success(f"You win ${st.session_state.total_bet}!")
        update_profile("win", st.session_state.total_bet)
        st.session_state.game_result = "win"
    elif dealer_val > player_val:
        st.error(f"You lose ${st.session_state.total_bet}!")
        update_profile("lose", st.session_state.total_bet)
        st.session_state.game_result = "lose"
    else:
        st.info("It's a tie! Push.")
        update_profile("tie", st.session_state.total_bet)
        st.session_state.game_result = "tie"
    
    show_game_end()

def show_game_end():
    """Show options after game ends"""
    st.subheader("Game Over")
    
    # Updated balance
    st.info(f"New balance: ${st.session_state.current_user['balance']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Play Again", type="primary"):
            # Reset game state
            st.session_state.player_hand = []
            st.session_state.bot_hand = []
            st.session_state.total_bet = 0
            st.session_state.player_value = 0
            st.session_state.dealer_value = 0
            st.session_state.game_result = None
            st.session_state.dealer_turn_complete = False
            st.session_state.game_updated = False  # Reset the update flag
            st.session_state.game_phase = 'betting'
            st.rerun()
    
    with col2:
        if st.button("View Stats"):
            show_stats()
    
    with col3:
        if st.button("Logout"):
            st.session_state.current_user = None
            st.session_state.game_phase = 'login'
            st.session_state.login_step = 'username'  # Reset login step
            st.session_state.entered_username = ""
            st.rerun()

def show_stats():
    """Display player statistics"""
    user = st.session_state.current_user
    st.subheader(f"{user['username']}'s Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Balance", f"${user['balance']}")
        st.metric("Games Played", user['games_played'])
        st.metric("Games Won", user['games_won'])
    
    with col2:
        win_rate = (user['games_won']/max(1,user['games_played'])*100)
        st.metric("Win Rate", f"{win_rate:.1f}%")
        st.metric("Total Winnings", f"${user['total_winnings']}")
        st.metric("Biggest Win", f"${user['biggest_win']}")
    
    st.write(f"**Account Created:** {user['created']}")

def admin_login_page():
    """Admin login interface"""
    st.subheader("🔐 Admin/Cashier Login")
    
    if not st.session_state.admin_mode:
        admin_username = st.text_input("Admin Username:", key="admin_username")
        admin_password = st.text_input("Admin Password:", type="password", key="admin_password")
        
        if st.button("Admin Login", key="admin_login_btn"):
            if admin_password == ADMIN_PASSWORD:
                st.session_state.admin_mode = True
                st.session_state.admin_user = admin_username
                st.session_state.game_phase = 'admin'
                st.success(f"Welcome, {admin_username}!")
                st.rerun()
            else:
                st.error("Invalid password!")
    else:
        st.success("Already logged in as admin")
        if st.button("Go to Admin Panel"):
            st.session_state.game_phase = 'admin'
            st.rerun()

def admin_panel():
    """Admin panel for managing credits and transactions"""
    st.title("🏪 Admin Panel - Credit Management")
    
    # Admin info
    st.info(f"Logged in as: {st.session_state.admin_user}")
    
    col1, col2 = st.columns(2)
    with col2:
        if st.button("Logout Admin"):
            st.session_state.admin_mode = False
            st.session_state.admin_user = None
            st.session_state.game_phase = 'login'
            st.rerun()
    
    tabs = st.tabs(["💰 Add Credits", "📊 Transaction History", "👥 User Management", "💳 Payment Methods"])
    
    with tabs[0]:
        add_credits_interface()
    
    with tabs[1]:
        transaction_history()
    
    with tabs[2]:
        user_management()
    
    with tabs[3]:
        payment_methods_info()

def add_credits_interface():
    """Interface for adding credits to user accounts"""
    st.subheader("Add Credits to Player Account")
    
    profiles = load_profiles()
    if not profiles:
        st.warning("No players registered yet!")
        return
    
    # Select user
    usernames = list(profiles.keys())
    selected_user = st.selectbox("Select Player:", usernames)
    
    # Show current balance
    current_balance = profiles[selected_user]['balance']
    st.info(f"Current Balance: ${current_balance}")
    
    # Credit amount
    col1, col2 = st.columns(2)
    with col1:
        credit_amount = st.number_input("Credits to Add ($):", min_value=1, max_value=1000, step=1, value=50)
    
    with col2:
        payment_method = st.selectbox("Payment Method:", 
                                    ["Cash", "Credit Card", "Debit Card", "Venmo", "PayPal", "Zelle", "Gift Card"])
    
    # Transaction note
    transaction_note = st.text_area("Transaction Note (optional):", 
                                  placeholder="e.g., Customer paid with $50 cash")
    
    # Preview
    st.subheader("Transaction Preview")
    new_balance = current_balance + credit_amount
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Balance", f"${current_balance}")
    with col2:
        st.metric("Adding", f"${credit_amount}")
    with col3:
        st.metric("New Balance", f"${new_balance}")
    
    # Confirm transaction
    if st.button("💳 Process Payment & Add Credits", type="primary"):
        # Update user balance
        profiles[selected_user]['balance'] += credit_amount
        save_profiles(profiles)
        
        # Log transaction
        transaction = log_transaction(
            username=selected_user,
            amount=credit_amount,
            payment_method=payment_method,
            transaction_type="credit_purchase"
        )
        
        # Show success
        st.success(f"✅ Successfully added ${credit_amount} to {selected_user}'s account!")
        st.success(f"New balance: ${profiles[selected_user]['balance']}")
        st.info(f"Transaction ID: #{transaction['id']}")
        
        # Auto-refresh after 2 seconds
        time.sleep(2)
        st.rerun()

def transaction_history():
    """Display transaction history"""
    st.subheader("Transaction History")
    
    transactions = load_transactions()
    if not transactions:
        st.info("No transactions yet.")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_user = st.selectbox("Filter by User:", ["All Users"] + [t['username'] for t in transactions])
    with col2:
        filter_payment = st.selectbox("Filter by Payment:", ["All Methods"] + list(set([t['payment_method'] for t in transactions])))
    with col3:
        show_recent = st.selectbox("Show:", ["All Transactions", "Today Only", "This Week"])
    
    # Apply filters
    filtered_transactions = transactions
    if filter_user != "All Users":
        filtered_transactions = [t for t in filtered_transactions if t['username'] == filter_user]
    if filter_payment != "All Methods":
        filtered_transactions = [t for t in filtered_transactions if t['payment_method'] == filter_payment]
    
    # Display transactions
    st.write(f"Showing {len(filtered_transactions)} transactions")
    
    for transaction in reversed(filtered_transactions[-50:]):  # Show last 50
        with st.expander(f"#{transaction['id']} - {transaction['username']} - ${transaction['amount']} - {transaction['timestamp']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Player:** {transaction['username']}")
                st.write(f"**Amount:** ${transaction['amount']}")
                st.write(f"**Payment:** {transaction['payment_method']}")
            with col2:
                st.write(f"**Type:** {transaction['transaction_type']}")
                st.write(f"**Time:** {transaction['timestamp']}")
                st.write(f"**Admin:** {transaction['admin']}")
    
    # Transaction summary
    st.subheader("Summary")
    total_credits_sold = sum([t['amount'] for t in filtered_transactions if t['transaction_type'] == 'credit_purchase'])
    st.metric("Total Credits Sold", f"${total_credits_sold}")

def user_management():
    """User management interface"""
    st.subheader("User Management")
    
    profiles = load_profiles()
    if not profiles:
        st.info("No users registered yet.")
        return
    
    # User list with balances
    for username, profile in profiles.items():
        with st.expander(f"{username} - Balance: ${profile['balance']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Games Played:** {profile['games_played']}")
                st.write(f"**Games Won:** {profile['games_won']}")
                st.write(f"**Win Rate:** {(profile['games_won']/max(1,profile['games_played'])*100):.1f}%")
            with col2:
                st.write(f"**Total Winnings:** ${profile['total_winnings']}")
                st.write(f"**Biggest Win:** {profile['biggest_win']}")
                st.write(f"**Created:** {profile['created']}")
            with col3:
                # Admin actions
                new_balance = st.number_input(f"Set Balance for {username}:", 
                                            value=profile['balance'], 
                                            key=f"balance_{username}")
                if st.button(f"Update Balance", key=f"update_{username}"):
                    old_balance = profile['balance']
                    profiles[username]['balance'] = new_balance
                    save_profiles(profiles)
                    
                    # Log the balance change
                    log_transaction(
                        username=username,
                        amount=new_balance - old_balance,
                        payment_method="Admin Adjustment",
                        transaction_type="balance_adjustment"
                    )
                    
                    st.success(f"Updated {username}'s balance to ${new_balance}")
                    st.rerun()

def user_admin_panel():
    """User admin panel - accessible only to admin users"""
    st.title("👑 User Admin Panel")
    
    user = st.session_state.current_user
    st.info(f"Logged in as: {user['username']} (Admin)")
    
    # Back button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Game"):
            st.session_state.game_phase = 'betting'
            st.rerun()
    with col2:
        if st.button("Logout"):
            st.session_state.current_user = None
            st.session_state.game_phase = 'login'
            st.session_state.login_step = 'username'
            st.session_state.entered_username = ""
            st.rerun()
    
    # Admin features tabs
    tabs = st.tabs(["👥 User Management", "📊 Game Statistics", "💰 Credit Management", "🔧 Admin Tools"])
    
    with tabs[0]:
        user_admin_management()
    
    with tabs[1]:
        game_statistics_overview()
    
    with tabs[2]:
        credit_management_admin()
    
    with tabs[3]:
        admin_tools()

def user_admin_management():
    """User management for admin users"""
    st.subheader("User Management")
    
    profiles = load_profiles()
    if not profiles:
        st.info("No users registered yet.")
        return
    
    # Summary stats
    total_users = len(profiles)
    total_balance = sum(p['balance'] for p in profiles.values())
    admin_users = sum(1 for p in profiles.values() if p.get('is_admin', False))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Total Balance", f"${total_balance}")
    with col3:
        st.metric("Admin Users", admin_users)
    
    # User list with admin controls
    st.subheader("All Users")
    for username, profile in profiles.items():
        is_admin = profile.get('is_admin', False)
        admin_badge = " 👑" if is_admin else ""
        
        with st.expander(f"{username}{admin_badge} - Balance: ${profile['balance']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Username:** {profile['username']}")
                st.write(f"**Balance:** ${profile['balance']}")
                st.write(f"**Games Played:** {profile['games_played']}")
                st.write(f"**Games Won:** {profile['games_won']}")
                win_rate = (profile['games_won']/max(1,profile['games_played'])*100)
                st.write(f"**Win Rate:** {win_rate:.1f}%")
            
            with col2:
                st.write(f"**Total Winnings:** ${profile['total_winnings']}")
                st.write(f"**Biggest Win:** ${profile['biggest_win']}")
                st.write(f"**Created:** {profile['created']}")
                st.write(f"**Admin Status:** {'Yes' if is_admin else 'No'}")
            
            with col3:
                st.write("**Admin Actions:**")
                
                # Balance adjustment
                new_balance = st.number_input(
                    "Set Balance:", 
                    value=profile['balance'], 
                    key=f"admin_balance_{username}",
                    min_value=0
                )
                
                if st.button("Update Balance", key=f"admin_update_{username}"):
                    old_balance = profile['balance']
                    profiles[username]['balance'] = new_balance
                    save_profiles(profiles)
                    
                    # Log the change
                    log_transaction(
                        username=username,
                        amount=new_balance - old_balance,
                        payment_method="Admin Adjustment",
                        transaction_type=f"balance_adjustment_by_{st.session_state.current_user['username']}"
                    )
                    
                    st.success(f"Updated {username}'s balance to ${new_balance}")
                    st.rerun()
                
                # Admin status toggle
                if username != st.session_state.current_user['username']:  # Can't change own admin status
                    current_admin = profile.get('is_admin', False)
                    new_admin_status = st.checkbox(
                        "Admin Privileges", 
                        value=current_admin, 
                        key=f"admin_status_{username}"
                    )
                    
                    if new_admin_status != current_admin:
                        if st.button("Update Admin Status", key=f"admin_toggle_{username}"):
                            profiles[username]['is_admin'] = new_admin_status
                            save_profiles(profiles)
                            status_text = "granted" if new_admin_status else "revoked"
                            st.success(f"Admin privileges {status_text} for {username}")
                            st.rerun()

def game_statistics_overview():
    """Game statistics overview for admins"""
    st.subheader("Game Statistics Overview")
    
    profiles = load_profiles()
    transactions = load_transactions()
    
    if not profiles:
        st.info("No game data available yet.")
        return
    
    # Calculate stats
    total_games = sum(p['games_played'] for p in profiles.values())
    total_winnings = sum(p['total_winnings'] for p in profiles.values())
    avg_win_rate = sum((p['games_won']/max(1,p['games_played'])*100) for p in profiles.values()) / len(profiles)
    
    # Display main stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Games Played", total_games)
    with col2:
        st.metric("Total Player Winnings", f"${total_winnings}")
    with col3:
        st.metric("Average Win Rate", f"{avg_win_rate:.1f}%")
    with col4:
        house_edge = ((total_games * 50) - total_winnings) if total_games > 0 else 0  # Rough calculation
        st.metric("Estimated House Edge", f"${house_edge}")
    
    # Top players
    st.subheader("Top Players")
    sorted_players = sorted(profiles.values(), key=lambda x: x['balance'], reverse=True)
    
    for i, player in enumerate(sorted_players[:5], 1):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            admin_badge = " 👑" if player.get('is_admin', False) else ""
            st.write(f"{i}. {player['username']}{admin_badge}")
        with col2:
            st.write(f"${player['balance']}")
        with col3:
            st.write(f"{player['games_played']} games")
        with col4:
            win_rate = (player['games_won']/max(1,player['games_played'])*100)
            st.write(f"{win_rate:.1f}% win rate")

def credit_management_admin():
    """Credit management for admin users"""
    st.subheader("Credit Management")
    
    profiles = load_profiles()
    transactions = load_transactions()
    
    # Quick add credits
    st.subheader("Quick Add Credits")
    usernames = list(profiles.keys()) if profiles else []
    
    if usernames:
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_user = st.selectbox("Select User:", usernames, key="quick_credit_user")
        with col2:
            credit_amount = st.number_input("Credit Amount:", min_value=1, max_value=1000, value=50, key="quick_credit_amount")
        with col3:
            if st.button("Add Credits", key="quick_add_credits"):
                profiles[selected_user]['balance'] += credit_amount
                save_profiles(profiles)
                
                # Log transaction
                log_transaction(
                    username=selected_user,
                    amount=credit_amount,
                    payment_method="Admin Quick Add",
                    transaction_type=f"quick_credit_by_{st.session_state.current_user['username']}"
                )
                
                st.success(f"Added ${credit_amount} to {selected_user}'s account!")
                st.rerun()
    
    # Transaction summary
    if transactions:
        st.subheader("Recent Transactions")
        recent_transactions = transactions[-10:]  # Last 10 transactions
        
        for transaction in reversed(recent_transactions):
            st.write(f"**#{transaction['id']}** - {transaction['username']} - ${transaction['amount']} ({transaction['payment_method']}) - {transaction['timestamp']}")

def admin_tools():
    """Administrative tools"""
    st.subheader("Administrative Tools")
    
    # Backup/Export Data
    st.subheader("🔄 Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export User Data"):
            profiles = load_profiles()
            if profiles:
                # Create downloadable JSON
                import json
                data_str = json.dumps(profiles, indent=2)
                st.download_button(
                    label="Download User Data (JSON)",
                    data=data_str,
                    file_name=f"blackjack_users_backup_{time.strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No user data to export")
    
    with col2:
        if st.button("📥 Export Transaction Data"):
            transactions = load_transactions()
            if transactions:
                import json
                data_str = json.dumps(transactions, indent=2)
                st.download_button(
                    label="Download Transaction Data (JSON)",
                    data=data_str,
                    file_name=f"blackjack_transactions_backup_{time.strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No transaction data to export")
    
    # System Info
    st.subheader("🖥️ System Information")
    st.write(f"**Current Admin:** {st.session_state.current_user['username']}")
    st.write(f"**Server Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    profiles = load_profiles()
    transactions = load_transactions()
    
    st.write(f"**Total Users:** {len(profiles) if profiles else 0}")
    st.write(f"**Total Transactions:** {len(transactions) if transactions else 0}")
    
    # Danger Zone
    st.subheader("⚠️ Danger Zone")
    st.error("**WARNING:** These actions cannot be undone!")
    
    if st.button("🗑️ Clear All Transaction History", key="clear_transactions"):
        if st.button("⚠️ CONFIRM: Clear All Transactions", key="confirm_clear_transactions"):
            save_transactions([])
            st.success("All transaction history cleared!")
            st.rerun()

def payment_methods_info():
    """Information about accepted payment methods"""
    st.subheader("Accepted Payment Methods")
    
    payment_info = {
        "💵 Cash": "Accept physical cash payments. Always count carefully and provide receipt.",
        "💳 Credit Card": "Accept major credit cards. Ensure card is valid and signature matches.",
        "💳 Debit Card": "Accept debit cards with PIN verification when possible.",
        "📱 Venmo": "Digital payment via Venmo app. Verify payment received before adding credits.",
        "💰 PayPal": "Accept PayPal payments. Check for payment confirmation.",
        "🏦 Zelle": "Bank-to-bank transfer. Verify payment in bank account.",
        "🎁 Gift Card": "Accept valid gift cards. Check balance before processing."
    }
    
    for method, description in payment_info.items():
        st.write(f"**{method}**")
        st.write(f"_{description}_")
        st.write("")
    
    st.info("💡 **Tip:** Always verify payment before adding credits to player accounts!")
    
    # Quick stats
    transactions = load_transactions()
    if transactions:
        st.subheader("Payment Method Statistics")
        payment_stats = {}
        for transaction in transactions:
            method = transaction['payment_method']
            payment_stats[method] = payment_stats.get(method, 0) + transaction['amount']
        
        for method, total in payment_stats.items():
            st.write(f"**{method}:** ${total}")
    """Information about accepted payment methods"""
    st.subheader("Accepted Payment Methods")
    
    payment_info = {
        "💵 Cash": "Accept physical cash payments. Always count carefully and provide receipt.",
        "💳 Credit Card": "Accept major credit cards. Ensure card is valid and signature matches.",
        "💳 Debit Card": "Accept debit cards with PIN verification when possible.",
        "📱 Venmo": "Digital payment via Venmo app. Verify payment received before adding credits.",
        "💰 PayPal": "Accept PayPal payments. Check for payment confirmation.",
        "🏦 Zelle": "Bank-to-bank transfer. Verify payment in bank account.",
        "🎁 Gift Card": "Accept valid gift cards. Check balance before processing."
    }
    
    for method, description in payment_info.items():
        st.write(f"**{method}**")
        st.write(f"_{description}_")
        st.write("")
    
    st.info("💡 **Tip:** Always verify payment before adding credits to player accounts!")
    
    # Quick stats
    transactions = load_transactions()
    if transactions:
        st.subheader("Payment Method Statistics")
        payment_stats = {}
        for transaction in transactions:
            method = transaction['payment_method']
            payment_stats[method] = payment_stats.get(method, 0) + transaction['amount']
        
        for method, total in payment_stats.items():
            st.write(f"**{method}:** ${total}")

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Initialize shoe if empty
    if not st.session_state.shoe:
        init_shoe()
    
    # Route to appropriate page based on game phase
    if st.session_state.game_phase == 'login':
        login_page()
    elif st.session_state.game_phase == 'betting':
        betting_page()
    elif st.session_state.game_phase == 'playing':
        playing_page()
    elif st.session_state.game_phase == 'admin':
        admin_panel()
    elif st.session_state.game_phase == 'user_admin':
        user_admin_panel()

# Run the app
if __name__ == "__main__":
    main()