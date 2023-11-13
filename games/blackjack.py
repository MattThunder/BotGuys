"""Blackjack game module

Contains all the logic needed to run a game of Blackjack.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import Card
from util import generate_deck
import random

class BJDeck:
    def __init__(self):
        

class BJHand:
    def __init__(self):


class BlackjackPlayer(BasePlayer):
    def __init__(self, hand, chips=300):
        super.__init__()

        self.hand = []
        self.chips = chips


class BlackjackGame(BaseGame):
    """
    Blackjack game model class. Keeps track of the deck and none else
    """
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=1, player_data={}, game_state=1)

        self.turn_order = []
        self.deck = generate_deck()
        self.dealer_hand = []
        random.shuffle(self.deck)

    #def __repr__(self):
 
        
class BlackjackManager(GameManager):
    def __init__(self, factory, channel_id, user_id):
        super().__init__(game=BlackjackGame(), base_gui=BlackjackButtonsBase(self),
                         channel_id=channel_id, factory=factory)
    
    async def start_game(self, interaction):
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        self.base_gui = BlackjackButtonsBaseGame(self)
        
    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Welcome to this game of Blackjack. Feel free to join."
        elif self.game.game_state == 4:
            return "Game has started, placeholder string"
        return "You shouldn't be seeing this."

    async def hit_user(self, interaction):
        """
        Adds a card to the user's hand
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return
        
        # add a card to the user's hand
        card = self.game.deck.pop()
        self.game.player_data[interaction.user]["hand"].append(card)
        
        # resend the base menu with the updated game state
        await self.resend(interaction)

    async def stand_user(self, interaction):
        """
        Ends the user's turn
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return
        
        # more interaction to be added to actually make it go to the next player
        
        # resend the base menu with the updated game state
        await self.resend(interaction)

    async def gameplay_loop(self):
        """
        The main gameplay loop for the Blackjack game
        """
        rounds = 3 # Temporary, 3 rounds of gameplay
        for round in range(rounds):
            # Get Dealer's Hand
            self.game.dealer_hand.append(self.game.deck.pop())

            #TODO add code here to send message indicating dealer hand
            
            player_turn_list = list(range(self.game.players))
            for turn in player_turn_list:
                #Iterates through dict of player data to find the turn
                current_user = [x for x in self.game.player_data if x["turn"] == turn][0]

                while(True):
                    # Break if they bust, stand, or reach 21
                    view = HitOrStand(self)
                    await current_user.send_message("Hit or Stand?", view=view, ephemeral=True)
                    await view.wait() # Wait for user to press a button
                    user_hand = current_user["hand"]
                    user_hand_value = bj_add(user_hand)
                    if bj_add(user_hand) > 21:
                        # Bust
                        break
                    elif bj_add(user_hand) == 21:
                        # Blackjack
                        break
                    else:
                        # Hit
                        continue
                    #TODO add code to detect if user stood and break
                    





     
class BlackjackButtonsBase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the hit or miss menu. This menu
        will be deleted after it is interacted with or 60 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")

        indi_player_data = BlackjackPlayer(hand=[], chips=300)
        await self.manager.add_player(interaction, indi_player_data)
    
    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        self.manager.remove_player(interaction)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.manager.quit_game(interaction)

    @discord.ui.button(label = "Start game", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.start_game(interaction)


class BlackjackButtonsBaseGame(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Resend", style = discord.ButtonStyle.gray)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Resend base menu message
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # resend
        await self.manager.resend(interaction)


class HitOrStand(discord.ui.View):
    """
    Button group used for the Blackjack game when the user can Hit or Stand as their options
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Hit Me", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Call hit_user
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        await self.manager.hit_user(interaction)

    @discord.ui.button(label = "Stand", style = discord.ButtonStyle.blurple)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Call stand_user
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        await self.manager.stand_user(interaction)
        
        
def bj_add(cards):
    """
    cards is a list of Card objects
    returns an integer corresponding to the value of the hand in
    a game of blackjack
    """
    total = 0
    ace_count = 0
    faces = ('A', 'J', 'Q', 'K')
    for card in cards:
        if card.face not in faces:
            total += int(card.face)
        elif card.face in faces[1:]:
            total += 10
        else:
            ace_count += 1
    total += 11 * ace_count
    for ace in range(ace_count):
        if total > 21:
            total -= 10
    return total

def play_bj(deck, action):
    """
    Simulates a player playing Blackjack.
    deck is the current game's deck
    action is the player's action
    """
    hand_visible = []
    hand_flipped = []
    bust = False
    while hand_visible.count < 2:
        c = deck[random.randint(0, deck.count - 1)]
        hand_visible.add(c)
        deck.remove(c)
    
    while not bust:
        if action == "Hit":
            c = deck[random.randint(0, deck.count - 1)]
            hand_visible.add(c)
            deck.remove(c)
            if bj_add(hand_visible) > 21:
                bust = True
            continue
        
        if action == "Double Down" and bj_add(hand_visible) in range(9, 12):
            # Doubles bet
            c = deck[random.randint(0, deck.count - 1)]
            hand_flipped.add(c)
            deck.remove(c)
            break
        
        if action == "Stand":
            break



# This method takes a hand as a parameter
#       A hand is a list of Card objects
# The function executes the flowchart logic of the dealer
#       Hit on 16 or less
#       Stand on 17 or greater
# Then the method returns a decision as a string:
#      "Hit" or "Stand"
def AI_Decision(hand):
    score = 0
    for card in hand:
        v = card.value
        if v=='A': continue # Skip aces for now, come back to this
        if v=='J' or v=='Q' or v=='K': score += 10
        else: score += int(v)

    for card in hand: # Let's work out aces now
        v = card.value
        if v=='A' and score+11 <= 21: score += 11
        else: score += 1

    if score < 17: return "Hit"
    if score > 16: return "Stand"
