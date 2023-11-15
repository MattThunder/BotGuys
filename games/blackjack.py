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
from util import STANDARD_52_DECK
from util import cards_to_str_52_standard
import random


class BlackjackPlayer(BasePlayer):
    def __init__(self):
        super().__init__()

        self.hand = []
        self.chips = 300
        self.current_bet = 0


class BlackjackGame(BaseGame):
    """
    Blackjack game model class. Keeps track of the turn order and dealer's hand
    """
    def __init__(self, cpus):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=1, player_data={}, game_state=1, cpus=cpus)

        self.turn_order = []
        self.dealer_hand = []

    #def __repr__(self):
 
        
class BlackjackManager(GameManager):
    def __init__(self, factory, channel, cpus):
        super().__init__(game=BlackjackGame(cpus), base_gui=BlackjackButtonsBase(self),
                         channel=channel, factory=factory)

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
        if self.game.game_state != 1:
            interaction.response.send_message("This game has already started.",
                                              ephemeral = True, delete_after = 10)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        # swap default GUI to active game buttons
        await interaction.channel.send(f"{interaction.user} started the game!")
        self.base_gui = BlackjackButtonsBetPhase(self)


        # draw 2 cards for the dealer and every player
        self.game.dealer_hand.extend(STANDARD_52_DECK.draw(1))
        for i in self.game.player_data:
            self.game.player_data[i].hand.extend(STANDARD_52_DECK.draw(2))
        await self.resend(interaction)

    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Who's ready for a game of blackjack?"
        elif self.game.game_state >= 4:
            ret = f"Dealer hand: {cards_to_str_52_standard(self.game.dealer_hand)}, ??\n"
            for player in self.game.turn_order:
                ret += (f"{player.mention} ({self.game.player_data[player].chips} chips): "
                f"{cards_to_str_52_standard(self.game.player_data[player].hand)}\n")
            return ret
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

        indi_player_data = BlackjackPlayer()
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


class BlackjackButtonsBaseGame(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

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


class BlackjackBetModal(discord.ui.Modal, title="Bet"):
    def __init__(self, manager, player):
        self.manager = manager
        self.player = player

    bet_box = discord.ui.TextInput(label="Enter bet...", max_length=4, default="5")

    async def on_submit(self, interaction: discord.Interaction):
        """
        testing
        """
        user_data = str(bet_box)


class BlackjackButtonsBetPhase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Bet!", style = discord.ButtonStyle.green)
    async def bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Allows the user to bring up the betting menu
        """
        print(f"{interaction.user} pressed {button.label}!")
        await interaction.response.send_modal(BlackjackBetModal(self.manager, interaction.user))



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
        if card.value not in faces:
            total += int(card.value)
        elif card.vale in faces[1:]:
            total += 10
        else:
            ace_count += 1
    total += 11 * ace_count
    for ace in range(ace_count):
        if total > 21:
            total -= 10
    return total