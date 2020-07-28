import discord
from discord.ext import commands, tasks
import sqlite3
import asyncio
import random
import datetime
import sys
from collections import Counter
from itertools import repeat
import os
# -*- coding: utf-8 -*-
bot = commands.Bot(command_prefix="", case_insensitive=True)
NAME_OF_THE_POINTS = 'points'   # Set name of the points
main_client_id = "INSERT ID FOR THE BOT"

base_channel = "" # Name of the main channel(str)
bots_channel = ""   # Bots channel(str)
kasyno_channel = ""   # Casino channel(str)
role_acessed = ""  # Role with acces to the bot(str)
base_guild_id = 0  # Guild id(int)

MUTE_TIME = 120
COOLDOWN_FOR_MESSAGE = 10
COST_OF_MUTE = 70
HOUR_TO_ROLL = "12:50"
WHEN_TO_RESET_DAILY = "00:00"
DAILY_AMOUNT = 30
JACKPOT_TIME = 30   # Seconds
spam_users = {}
USERS_IN_VOICE_CHANNELS = {}
EMOJIS_TO_REACT = ["<:black1:725831207937638420>", "<:braindead:721495732099743794>", "<:emoji_10:721424831022759946>", "<:D_:702569300803715073>"]


class Helpers:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

    @staticmethod
    def in_channel_base(ctx, channel=base_channel):
        if ctx.message.channel.name == channel:
            return True
        else:
            return False

    @staticmethod
    def in_channel_bots(ctx, channel=bots_channel):
        if ctx.message.channel.name == channel:
            return True
        else:
            return False

    @staticmethod
    def in_channel_casino(ctx, channel=kasyno_channel):
        if ctx.message.channel.name == channel:
            return True
        else:
            return False

    @staticmethod
    def in_channels_casino_bots(ctx):
        if ctx.message.channel.name == kasyno_channel or ctx.message.channel.name == bots_channel:
            return True
        else:
            return False

    @staticmethod
    def user_is_server_owner(ctx):
        return ctx.message.author == bot.get_guild(base_guild_id).owner

    @staticmethod
    def get_voice_channels():
        voice_channels = []
        for channel in bot.get_all_channels():
            if type(channel) == discord.channel.VoiceChannel:
                voice_channels.append(channel)
        return voice_channels

    @staticmethod
    def get_voice_clients():
        voice_clients = []
        for channel in bot.get_all_channels():
            if type(channel) == discord.channel.VoiceChannel:
                if str(channel) == "AFK #1":
                    continue
                for user in channel.members:
                    voice_clients.append(user)
        return voice_clients

    @staticmethod
    async def check_users_and_update_database():
        guild = bot.get_guild(base_guild_id)
        for roles_in_guild in guild.roles:
            if str(roles_in_guild) == role_acessed:
                members = roles_in_guild.members
                for member_in_role in members:
                    print(f"Fetching user: {member_in_role}....")
                    users_in_database = misc.get_all_user()
                    if (str(member_in_role),) in users_in_database:
                        print("User in database")
                    else:
                        print("User not in database!")
                        print("Adding user to the database!")
                        await misc.add_user(str(member_in_role))

    @staticmethod
    def check_if_user_in_main_role(user):
        guild = bot.get_guild(base_guild_id)
        for role_in_guild in guild.roles:
            if not str(role_in_guild) == role_acessed:
                continue
            members_in_role = role_in_guild.members
            if user in members_in_role:
                return True
            else:
                return False

    def get_jsz_count(self):
        return self.cursor.execute("SELECT amount FROM global_counter WHERE counter_name=:name",
                                   {"name": f"global_{NAME_OF_THE_POINTS}"}).fetchone()[0]

    async def update_jsz_count(self, amount=1):
        self.cursor.execute("UPDATE global_counter SET amount = amount + :amount WHERE counter_name = :name",
                            {"amount": amount, "name": f"global_{NAME_OF_THE_POINTS}"})
        self.conn.commit()

    def update_balance_for_user(self, user, amount=1):
        if self.check_if_user_exists_in_db(user):
            self.cursor.execute("UPDATE users SET amount = amount + :amount WHERE discord = :user",
                                {"amount": amount, "user": user})
            self.conn.commit()

    def remove_balance_for_user(self, user, amount):
        if self.check_if_user_exists_in_db(user):
            self.cursor.execute("UPDATE users SET amount = amount - :amount WHERE discord = :user",
                                {"amount": amount, "user": user})
            self.conn.commit()

    def get_balance_for_user(self, user):
        if self.check_if_user_exists_in_db(user):
            return int(self.cursor.execute("SELECT amount FROM users WHERE discord = :user", {"user": user}).fetchone()[0])

    def get_daily_for_user(self, user):
        if self.check_if_user_exists_in_db(user):
            return bool(self.cursor.execute("SELECT daily FROM users WHERE discord = :user", {"user": user}).fetchone()[0])

    def change_daily_for_user(self, user):
        if self.check_if_user_exists_in_db(user):
            self.cursor.execute("UPDATE users SET daily = 0 WHERE discord = :user", {"user": str(user)})
            self.conn.commit()

    def reset_daily(self):
        self.cursor.execute("UPDATE users SET daily = 1")
        self.conn.commit()

    def get_top5(self):
        return self.cursor.execute("SELECT * FROM users order by amount desc LIMIT 5;").fetchall()

    def check_if_user_exists_in_db(self, user):
        if self.cursor.execute("SELECT discord FROM users WHERE discord=:user", {"user": str(user)}).fetchone():
            return True
        else:
            return False

    async def add_user(self, user, start_balance=0, daily_points=1):
        self.cursor.execute("INSERT INTO users VALUES (:user, :balance, :daily) ", {"user": user, "balance": start_balance, "daily": daily_points})
        self.conn.commit()

    def change_discount_user(self, who_discount, old_user):
        self.cursor.execute("UPDATE discount SET user=:new_user WHERE user=:old_user",
                            {"new_user": who_discount, "old_user": old_user})
        self.conn.commit()

    def get_discount_user(self):
        return self.cursor.execute("SELECT user FROM discount").fetchone()[0]

    async def reset_user(self, user):
        if self.check_if_user_exists_in_db(user):
            self.cursor.execute("UPDATE users SET amount=0 WHERE discord=:user", {"user": user})

    async def update_ruletka(self, color, amount=1):
        self.cursor.execute("UPDATE ruletka SET counter= counter + :amount WHERE color=:color", {"amount": amount, "color": color})
        self.conn.commit()

    def get_stats_ruletka(self):
        return self.cursor.execute("SELECT * FROM ruletka").fetchall()

    def insert_colors_into_db(self):
        colors = ["red", "black", "green"]
        for color in colors:
            self.cursor.execute("""INSERT OR IGNORE INTO ruletka(color, counter) VALUES (:color, 0)""", {"color": color})
            self.conn.commit()

    def execute_sql(self, command):
        self.cursor.execute(command)
        self.conn.commit()


    def check_db_integrity(self):
        print('Sprawdzanie tabeli "discount"....')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS discount (
                                            user TEXT)""")
        print('Sprawdzanie tabeli "users"....')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                                            discord TEXT,
                                            amount INTEGER,
                                            daily BOOLEAN NOT NULL DEFAULT true)""")
        print('Sprawdzanie tabeli "global_counter"....')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS global_counter(
                                            counter_name TEXT,
                                            amount INTEGER)""")
        print('Sprawdzanie tabeli "ruletka"....')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ruletka (
                                            color TEXT,
                                            counter INTEGER,
                                            UNIQUE(color))""")
        self.insert_colors_into_db()

    def get_all_user(self):
        return self.cursor.execute("SELECT discord FROM users").fetchall()

    def close(self):
        self.conn.commit()
        self.conn.close()


if os.name == "nt":
    misc = Helpers("Path to database")    # Windows
else:
    misc = Helpers("Path to database")    # Linux


class Jackpot:
    def __init__(self, time_to_roll):
        self.is_jackpot_running = False
        self.jackpot_users = []
        self.allow_betting = False
        self.winner = ""
        self.jackpot_time = time_to_roll

    def check_if_jackpot_is_running(self):
        return self.is_jackpot_running

    def get_winner(self):
        return self.winner

    def clear_jackpot_users(self):
        self.jackpot_users.clear()

    def shuffle_jackpot_users(self):
        random.shuffle(self.jackpot_users)

    def pick_winner(self):
        return random.choice(self.jackpot_users)

    def get_jackpot_pool(self):
        return len(self.jackpot_users)

    def reset_jackpot(self):
        self.winner = ""
        self.clear_jackpot_users()

    async def main(self, ctx):
        if self.check_if_jackpot_is_running():
            await ctx.send("**There is jackpot running, u can join existing one**")
            return
        self.is_jackpot_running = True
        self.reset_jackpot()
        self.allow_betting = True
        await ctx.send(f"**U have {self.jackpot_time} seconds to join the jackpot!**")
        await asyncio.sleep(self.jackpot_time)
        self.allow_betting = False
        if self.get_jackpot_pool() == 0:
            await ctx.send("**Not enough players in jackpot**")
            self.is_jackpot_running = False
            return
        await asyncio.sleep(2)  # Just to wait two seconds to complete all bets from users
        self.shuffle_jackpot_users()
        self.winner = self.pick_winner()
        print(f"Winner is: {self.winner} with pool {self.get_jackpot_pool()}")
        await ctx.send(f"**Won __||{self.winner}||__ with pool __{self.get_jackpot_pool()}__**!")
        misc.update_balance_for_user(self.winner, self.get_jackpot_pool())
        self.is_jackpot_running = False

    async def postaw(self, ctx, user, amount):
        if not self.allow_betting:
            await ctx.send("**Jackpot is already rolling, u cant join!**")
            return
        misc.remove_balance_for_user(user, amount)
        try:
            self.jackpot_users.extend(repeat(user, amount))
        except:
            await ctx.send(f"**Something went wrong!**")
            return
        await ctx.send(f"**User {user} put {amount} and joined the jackpot**")
        users_in_jackpot_list = Counter(self.jackpot_users).most_common()
        track_number_user = 0
        entire_string = "----------------------------------------\n"
        for person in users_in_jackpot_list:
            track_number_user += 1
            percent = round(100 * float(person[1]) / float(self.get_jackpot_pool()), 2)
            entire_string = entire_string + str(f"**{track_number_user}. {person[0]}  {percent}%**\n")
        await ctx.send(entire_string + "----------------------------------------")


class Roulette:
    def __init__(self):
        self.numbers = [i for i in range(15)]
        self.win_number = None
        self.color_win_number = None
        self.players_bet_on_red = {}
        self.players_bet_on_black = {}
        self.players_bet_on_green = {}
        self.time_to_bet = 30
        self.is_roulette_running = False
        self.allow_betting = False
        self.stop_roulette = False

    def get_color_number_win(self):
        if self.win_number == 0:
            return "green"
        elif self.win_number in [i for i in range(1, 8)]:
            return "red"
        elif self.win_number in [i for i in range(8, 15)]:
            return "black"
        else:
            return None

    def reset_roulette(self):
        self.players_bet_on_red.clear()
        self.players_bet_on_green.clear()
        self.players_bet_on_black.clear()
        self.win_number = None
        self.color_win_number = None

    def shuffle_numbers(self):
        random.shuffle(self.numbers)

    def pick_win_number(self):
        return random.choice(self.numbers)

    async def main(self, ctx):
        while True:
            self.reset_roulette()
            self.is_roulette_running = True
            if self.stop_roulette is True:
                await ctx.send("**Roulette stopped!**")
                self.stop_roulette = False
                self.is_roulette_running = False
                break
            await ctx.send("**U have 30 seconds to bet**")
            self.allow_betting = True
            await asyncio.sleep(30)
            self.allow_betting = False
            await asyncio.sleep(1)
            self.shuffle_numbers()
            self.win_number = self.pick_win_number()
            self.color_win_number = self.get_color_number_win()
            if self.color_win_number == "green":
                await ctx.send("**Won** :green_square:!")
                for user, amount in self.players_bet_on_green.items():
                    misc.update_balance_for_user(user, amount * 14)
            elif self.color_win_number == "red":
                await ctx.send("**Won** :red_square:!")
                for user, amount in self.players_bet_on_red.items():
                    misc.update_balance_for_user(user, amount * 2)
            elif self.color_win_number == "black":
                await ctx.send("**Won** <:black1:725831207937638420>!")
                for user, amount in self.players_bet_on_black.items():
                    misc.update_balance_for_user(user, amount * 2)
            await misc.update_ruletka(self.color_win_number)

    async def postaw(self, ctx, user, color, amount):
        if misc.get_balance_for_user(user) < amount:
            await ctx.send("**Not enough points!**")
            return

        if color not in ["g", "r", "b"]:
            await ctx.send("**Please provide right color!**")
            return

        if self.is_roulette_running is False:
            await ctx.send("**There is no roulette**")
            return

        if self.allow_betting is False:
            await ctx.send("**Roulette is rolling, u cant join!**")
            return
        if color == "g":
            try:
                self.players_bet_on_green[user] = self.players_bet_on_green[user] + amount
                await ctx.send(f"**User {user} put {amount} on Green**")
            except KeyError:
                self.players_bet_on_green[user] = amount
                await ctx.send(f"**User {user} put {amount} on Green**")
        elif color == "r":
            try:
                self.players_bet_on_red[user] = self.players_bet_on_red[user] + amount
                await ctx.send(f"**User {user} put {amount} on Red**")
            except KeyError:
                self.players_bet_on_red[user] = amount
                await ctx.send(f"**User {user} put {amount} on Red**")
        elif color == "b":
            try:
                self.players_bet_on_black[user] = self.players_bet_on_black[user] + amount
                await ctx.send(f"**User {user} put {amount} on Black**")
            except KeyError:
                self.players_bet_on_black[user] = amount
                await ctx.send(f"**User {user} put {amount} on Black**")

        misc.remove_balance_for_user(user, amount)


@bot.event
async def on_ready():
    misc.check_db_integrity()
    print('We have logged in as {0.user}'.format(bot))
    await misc.check_users_and_update_database()
    reset_daily.start()
    pick_random_user.start()
    count_seconds_for_each_user.start()


@tasks.loop(seconds=1)
async def count_seconds_for_each_user():
    await bot.wait_until_ready()
    global USERS_IN_VOICE_CHANNELS
    list_with_all_voice_clients = list(map(str, misc.get_voice_clients()))
    if not list_with_all_voice_clients:
        return
    for member in list_with_all_voice_clients:  # Count second for invidual users
        if member not in USERS_IN_VOICE_CHANNELS:
            USERS_IN_VOICE_CHANNELS[str(member)] = 1
        else:
            USERS_IN_VOICE_CHANNELS[str(member)] = USERS_IN_VOICE_CHANNELS[str(member)] + 1
    for user in list(USERS_IN_VOICE_CHANNELS.keys()):   # Copying to list to avoid "RuntimeError: dictionary changed size during iteration"
        if user not in list_with_all_voice_clients:     # Check if all user in dictionary are in voice channels
            USERS_IN_VOICE_CHANNELS.pop(user)
    for member, seconds in list(USERS_IN_VOICE_CHANNELS.items()):   # If 180 seconds passes give user 2 points
        if seconds % 180 == 0:  # 3 minutes
            misc.update_balance_for_user(member, 2)
            USERS_IN_VOICE_CHANNELS.pop(member)


@tasks.loop(seconds=1)
async def pick_random_user():
    await bot.wait_until_ready()
    if datetime.datetime.now().strftime("%H:%M") == HOUR_TO_ROLL:
        guild = bot.get_guild(base_guild_id)
        for role_in_guild in guild.roles:
            if not str(role_in_guild) == role_acessed:
                continue
            old_user = misc.get_discount_user()
            members = role_in_guild.members
            while True:
                who_discount = str(random.choice(members))
                if misc.get_balance_for_user(who_discount) >= 1:
                    misc.change_discount_user(who_discount, old_user)
                    break
                else:
                    continue
            for channel in bot.get_all_channels():
                if str(channel) == base_channel:
                    await channel.send(f"**Today discount is: {who_discount}**")
                    await asyncio.sleep(60)


@tasks.loop(seconds=1)
async def reset_daily():
    await bot.wait_until_ready()
    if datetime.datetime.now().strftime("%H:%M") == WHEN_TO_RESET_DAILY:
        print("Reseting daily...")
        misc.reset_daily()
        await asyncio.sleep(60)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('**Wait %.2fs**' % error.retry_after)


@bot.command(name="u_up", pass_context=True)
@commands.check(misc.in_channel_bots)
@commands.check(misc.user_is_server_owner)
async def u_up(ctx):
    await ctx.send("Updating database.....")
    await misc.check_users_and_update_database()


@bot.command(name="statistics_roulette", pass_context=True)
@commands.check(misc.user_is_server_owner)
@commands.check(misc.in_channels_casino_bots)
async def statistics_rulete(ctx):
    stats = misc.get_stats_ruletka()
    await ctx.send(f"**Statistics roulette: \nRed: {stats[0][1]}\nBlack: {stats[1][1]}\nGreen: {stats[2][1]} **")


@bot.command(name=f"add_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.check(misc.in_channel_bots)
@commands.check(misc.user_is_server_owner)
async def adder(ctx, member: discord.Member, amount: int):
    misc.update_balance_for_user(str(member), amount)


@bot.command(name=f"remove_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.check(misc.in_channel_bots)
@commands.check(misc.user_is_server_owner)
async def remover(ctx, member: discord.Member, amount: int):
    misc.remove_balance_for_user(str(member), amount)


@bot.command(name=f"reset_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.check(misc.in_channel_bots)
@commands.check(misc.user_is_server_owner)
async def reset(ctx, user: discord.Member):
    user_to_reset = str(user)
    await misc.reset_user(user_to_reset)
    await ctx.send("**RESET**")


@bot.command(name=f"exit_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.check(misc.in_channel_bots)
@commands.check(misc.user_is_server_owner)
async def fn_exit(ctx):
    await ctx.send("Exiting...")
    print("Exiting bot....")
    misc.close()
    sys.exit()


@bot.command(name=f"daily_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.cooldown(1, COOLDOWN_FOR_MESSAGE, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def daily(ctx):
    user = str(ctx.message.author)
    if misc.get_daily_for_user(user) is True:
        misc.update_balance_for_user(user, DAILY_AMOUNT)
        misc.change_daily_for_user(user)
        await ctx.send(f"**U just redemeed {DAILY_AMOUNT} {NAME_OF_THE_POINTS}**")
    else:
        await ctx.send("**U already redemeed your daily1**")


jackpot_brain = Jackpot(JACKPOT_TIME)


@bot.group(name="jackpot")
@commands.check(misc.in_channel_bots)
async def jackpot(ctx):
    pass


@jackpot.command(name="create", pass_context=True)
@commands.cooldown(1, 0.5, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def main_jackpot(ctx):
    await jackpot_brain.main(ctx)


@jackpot.command(name="put", pass_context=True)
@commands.cooldown(1, 0.5, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def place_bet(ctx, amount: int):
    author = str(ctx.message.author)
    if amount <= 0 or not isinstance(amount, int):
        await ctx.send("**Please provide correct number!**")
        return
    if not jackpot_brain.check_if_jackpot_is_running():
        await ctx.send("**No jackpot running atm!**")
        return
    if misc.get_balance_for_user(author) < amount:
        await ctx.send("**Not enough points!**")
        return
    await jackpot_brain.postaw(ctx, author, amount)


roulette = Roulette()
@bot.group(name="roulette")
@commands.check(misc.in_channel_casino)
async def roulette(ctx):
    pass


@jackpot.command(name="create", pass_context=True)
@commands.cooldown(1, 0.5, commands.BucketType.user)
@commands.check(misc.user_is_server_owner)
@commands.check(misc.in_channel_casino)
async def main_jackpot(ctx):
    if roulette.is_roulette_running is True:
        await ctx.send("**Roulette is already on!**")
        return
    await roulette.main(ctx)


@jackpot.command(name="stop", pass_context=True)
@commands.cooldown(1, 0.5, commands.BucketType.user)
@commands.check(misc.user_is_server_owner)
@commands.check(misc.in_channel_casino)
async def stop_rol(ctx):
    roulette.stop_roulette = True


@jackpot.command(name="put", pass_context=True)
@commands.cooldown(1, 0.5, commands.BucketType.user)
@commands.check(misc.in_channel_casino)
async def place_bet(ctx, color: str, amount: int):
    author = str(ctx.message.author)
    if amount <= 0 or not isinstance(amount, int):
        await ctx.send("**Please provide correct number!**")
        return
    await roulette.postaw(ctx, author, str(color), amount)


@bot.command(name=f"give_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.cooldown(1, COOLDOWN_FOR_MESSAGE, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def give(ctx, member_to_send_balance: discord.Member, amount: int):
    author = str(ctx.message.author)
    if int(amount) <= 0 or not isinstance(amount, int):
        await ctx.send("**Please provide correct number!**")
        return

    if misc.get_balance_for_user(author) < int(amount):
        await ctx.send("**Not enough points!**")
        return

    print(f"Uzytkownik {author} dal uzytkownikowi: {str(member_to_send_balance)} {amount} {NAME_OF_THE_POINTS}")
    misc.remove_balance_for_user(author, amount)
    misc.update_balance_for_user(str(member_to_send_balance), amount)
    await ctx.send(f"**User {author} gave to another user: {member_to_send_balance.mention} {amount} {NAME_OF_THE_POINTS}**")


@bot.command(name=f"{NAME_OF_THE_POINTS}", pass_context=True)
@commands.cooldown(1, COOLDOWN_FOR_MESSAGE, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def jsz(ctx):
    author = str(ctx.message.author)
    if author in spam_users and spam_users[author]["messages"] >= 7:   # 10
        if spam_users[author].get("warning_sent", False) is True:
            await ctx.send(
                f"**{ctx.message.author.mention} React on this message with emoji: '{spam_users[author]['emoji']}' in order to keep writing {NAME_OF_THE_POINTS}!**")
            return
        else:
            spam_users[author]["emoji"] = random.choice(EMOJIS_TO_REACT)
        spam_users[author]["warning_sent"] = True
        await ctx.send(f"**{ctx.message.author.mention} React on this message with emoji: '{spam_users[author]['emoji']}' in order to keep writing  {NAME_OF_THE_POINTS}!**")
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=lambda reaction, user: str(user) == author and str(reaction.emoji) == spam_users[author]["emoji"])
        except asyncio.TimeoutError:
            return
        spam_users.pop(author, None)
        return
    misc.update_balance_for_user(author)
    await misc.update_jsz_count()
    points_count = misc.get_jsz_count()
    await ctx.send(f"**{NAME_OF_THE_POINTS} numer |{points_count}|**")
    if author in spam_users:
        spam_users[author]["messages"] = spam_users[author]["messages"] + 1
    else:
        spam_users.clear()
        spam_users[author] = {}
        spam_users[author]["messages"] = 1



@bot.command(name=f"ranking_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.cooldown(1, COOLDOWN_FOR_MESSAGE, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def rank(ctx):
    lista_rank = misc.get_top5()
    await ctx.send(f"""**                                       Ranking: 
                                       1. {lista_rank[0][0]}    |{lista_rank[0][1]}|
                                       2. {lista_rank[1][0]}    |{lista_rank[1][1]}|
                                       3. {lista_rank[2][0]}    |{lista_rank[2][1]}|
                                       4. {lista_rank[3][0]}    |{lista_rank[3][1]}|
                                       5. {lista_rank[4][0]}    |{lista_rank[4][1]}|**""")



@bot.command(name=f"moje_{NAME_OF_THE_POINTS}", pass_context=True)
@commands.cooldown(1, COOLDOWN_FOR_MESSAGE, commands.BucketType.user)
@commands.check(misc.in_channels_casino_bots)
async def stats(ctx):
    user = str(ctx.message.author)
    balance = misc.get_balance_for_user(user)
    if not misc.check_if_user_exists_in_db(user):
        await ctx.send(f"**U dont have role: {role_acessed}**")
        return
    await ctx.send(f"""**Score** {ctx.author.mention} **is: {balance}**""")



@bot.command(name=f'mute_{NAME_OF_THE_POINTS}', pass_context=True)
@commands.cooldown(1, COOLDOWN_FOR_MESSAGE, commands.BucketType.user)
@commands.check(misc.in_channel_bots)
async def mute(ctx, member: discord.Member):
    author = str(ctx.message.author)
    person_to_mute = member
    if misc.get_balance_for_user(author) < COST_OF_MUTE and not str(person_to_mute) == misc.get_discount_user():
        await ctx.send("**Not enough points!**")
        return
    elif misc.get_balance_for_user(author) < COST_OF_MUTE / 2 and str(person_to_mute) == misc.get_discount_user():
        await ctx.send("**Not enough points!**")
        return

    if str(person_to_mute) == misc.get_discount_user():
        misc.remove_balance_for_user(author, COST_OF_MUTE / 2)
    else:
        misc.remove_balance_for_user(author, COST_OF_MUTE)
    print(f"User {author} muted: {person_to_mute}")
    await ctx.send("**Mutowanie**")
    await person_to_mute.edit(mute=True)
    await asyncio.sleep(MUTE_TIME)
    await person_to_mute.edit(mute=False)


if __name__ == '__main__':
    bot.run(main_client_id)
