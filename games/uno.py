"""Uno game module

Contains all the logic needed to run a game of Uno.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import Card
import random


class UnoPlayer(BasePlayer):
    def __init__(self):
        super().__init__()
    
        self.hand = []
        self.skipped = False
        
    def get_playable_cards(self, top_card):
        playable_cards = [card for card in self.hand if card.color == top_card.color or card.value == top_card.value or card.color == "Wild"]
        return playable_cards


class UnoGame(BaseGame):
    """
    Uno game model class. Keeps track of the deck and none else
    """
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=3, player_data={}, game_state=1)
        
        self.deck = generate_deck_uno()
        random.shuffle(self.deck)
        self.discard = []
        self.turn_order = []
        self.top_card = UnoCard("None", "")
      
        
class UnoManager(GameManager):
    def __init__(self, factory, channel_id, user_id):
        super().__init__(game=UnoGame(), base_gui=UnoButtonsBase(self),
                         channel_id=channel_id, factory=factory)
        
    async def add_player(self, interaction, init_player_data=None):
        await super().add_player(interaction, init_player_data)
        if interaction.user in self.game.player_data \
        and interaction.user not in self.game.turn_order:
            self.game.turn_order.append(interaction.user)

    async def remove_player(self, interaction):
        await super().remove_player(interaction)
        if interaction.user not in self.game.player_data \
        and interaction.user in self.game.turn_order:
            self.game.turn_order.remove(interaction.user)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.quit_game(interaction)
    
    async def start_game(self, interaction):
        if self.game.game_state == 4:
            interaction.response.send_message("This game has already started.",
                                              ephemeral = True, delete_after = 10)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        # swap default GUI to active game buttons
        self.base_gui = UnoButtonsBaseGame(self)
        # setup the game board
        self.setup()
        await self.resend(interaction)
        
    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Welcome to this game of Uno. Feel free to join."
        elif self.game.game_state == 4:
            output = f"Top Card: {card_to_emoji(self.game.top_card)}"
            return output
        return "Game has started!"
        
    def setup(self):
        for i in self.game.player_data:
            self.draw_cards(self.game.player_data[i], 7)

        # Assign the top-card. The game cannot begin on a "Reverse", "Skip", "Draw Two", or "Wild"
        print()
        print("Setting up the table...")
        while True:
            self.game.top_card = self.game.deck.pop()
            print(f"The top card is {self.game.top_card}. ", end="")
            top_card_is_valid = True
            if (self.game.top_card.value == "Reverse"): top_card_is_valid = False
            if (self.game.top_card.value == "Skip"): top_card_is_valid = False
            if (self.game.top_card.value == "Draw Two"): top_card_is_valid = False
            if (self.game.top_card.name == "Wild"): top_card_is_valid = False
            if not top_card_is_valid: 
                print("That's no good... Picking a new top card...")
            else:
                print("Let the game begin!")
                break
            
    def draw_cards(self, player, num_cards=1):
        for i in range(num_cards):
            if len(self.game.deck) == 0: 
                self.announce("The deck is empty! Regenerating deck...")
                self.regenerateDeck()
            card = self.game.deck.pop()
            player.hand.append(card)
            player.hand = sorted(player.hand)
    
    def get_player_hand(self, player):
        return self.game.player_data[player].hand


class UnoButtonsBase(discord.ui.View):
    """
    Base menu button group for the Uno game.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager    
    
    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the hit or miss menu. This menu
        will be deleted after it is interacted with or 10 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")

        indi_player_data = UnoPlayer()
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
        await self.manager.remove_player(interaction)
    
    @discord.ui.button(label = "Start Game", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.start_game(interaction)


class UnoButtonsBaseGame(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        
    @discord.ui.button(label = "Show Cards", style = discord.ButtonStyle.green)
    async def show_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the show cards menu. This menu
        will be deleted after it is interacted with or 20 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        print(f"{interaction.user} pressed {button.label}!")
            
        view = UnoCardButtons(self.manager, self.manager.get_player_hand(interaction.user))
        await interaction.response.send_message("Your cards:", view = view, ephemeral = True,
                                                delete_after = 20)
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the card button press (the UnoCardButtons UI message)
        await interaction.delete_original_response()
        
    @discord.ui.button(label = "Resend", style = discord.ButtonStyle.gray)
    async def resend(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Resend base menu message
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # resend
        await self.manager.resend(interaction)


class UnoCardButtons(discord.ui.View):
    """
    Creates private group of buttons representing the cards in a user's hand
    """
    def __init__(self, manager, player_hand):
        super().__init__()
        self.manager = manager
        self.player_hand = player_hand
        
        for i in range(len(self.player_hand)):
            self.add_item(CardButton(self.manager, self.player_hand[i]))

  
class CardButton(discord.ui.Button):
    """
    Button class that represents an individual card in a user's hand
    """
    def __init__(self, manager, card_name, disabled=True):
        super().__init__(style=discord.ButtonStyle.gray, label=f"{card_name.value}", emoji=color_to_emoji(card_name))
        self.manager = manager
        self.card_name = card_name
        self.disabled = disabled
        
    async def callback(self, interaction: discord.Interaction):
        print(f"{interaction.user} pressed {self.label}!")
        assert self.view is not None
        view: UnoCardButtons = self.view
    
        #TODO: Add code that places a card down/rejects chosen card
    
        self.disabled = True    
        view.stop()
        await interaction.response.send_message(f"You played {self.label}", ephemeral = True,
                                                delete_after = 10)


class UnoCard(Card):
    def __init__(self, name, value):
        super().__init__(name, value)
        
        self.priority = 0
        if self.name == "Red": self.priority += 0
        if self.name == "Blue": self.priority += 15
        if self.name == "Green": self.priority += 30
        if self.name == "Yellow": self.priority += 45
        if self.name == "Wild": self.priority += 60

        if self.value == "Reverse": self.priority += 11
        elif self.value == "Skip": self.priority += 12
        elif self.value == "Draw Two": self.priority += 13
        elif self.value == "Card": self.priority += 1
        elif self.value == "Draw Four": self.priority += 2
        elif self.value == "Wild": self.priority += 0
        elif self.value == "": self.priority += 0
        else: self.priority += int(self.value)
    
    def __str__(self):
        return f"{self.name} {self.value}"
    
    def __eq__(self, other):
        if not isinstance(other, Card): return False
        if self.name != other.name: return False
        if self.value != other.value: return False
        return True
    
    def __lt__(self, other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority
    
    
def generate_deck_uno():
    deck = []
    for color in ('Red', 'Yellow', 'Green', 'Blue'):
        deck.append(UnoCard(color, '0'))
        for value in range(1,10):
            deck.append(UnoCard(color, str(value)))
            deck.append(UnoCard(color, str(value)))
        for value in range(2):
            deck.append(UnoCard(color, "Draw Two"))
            deck.append(UnoCard(color, "Reverse"))
            deck.append(UnoCard(color, "Skip"))
    for value in range(4):
        deck.append(UnoCard("Wild", "Wild"))
        deck.append(UnoCard("Wild", "Draw Four"))
    return deck


def card_to_emoji(card):
    output = ""
    if card.name == "Red":
        output += ":red_circle: "
    elif card.name == "Yellow":
        output += ":yellow_circle: "
    elif card.name == "Green":
        output += ":green_circle: "
    elif card.name == "Blue":
        output += ":blue_circle: "
    elif card.name == "Wild":
        output += ":black_circle: "
    output += card.value
    return output


def color_to_emoji(card):
    if card.name == "Red":
        return "🔴"
    elif card.name == "Yellow":
        return "🟡"
    elif card.name == "Green":
        return "🟢"
    elif card.name == "Blue":
        return "🔵"
    elif card.name == "Wild":
        return "⚫"
    return "🟣"