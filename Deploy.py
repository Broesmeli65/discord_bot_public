import os
import discord
from dotenv import load_dotenv
import random
from discord.ext import commands
import asyncio
from asyncio import sleep
from collections import defaultdict
import yt_dlp
from collections import deque
from discord import ButtonStyle, ui


intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.voice_states = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

@bot.command(name='help')
async def help(ctx):
    commands = {
        'hallo': 'Says hallo back to you.',
        'play': 'Plays a song from a given URL.',
        'queue': 'Shows the current queue of songs.',
        'stop': 'Stops playback and disconnects from the voice channel.',
        'pause': 'Pauses playback.',
        'resume': 'Resumes playback.',
        'next': 'Skips to the next song in the queue.',
        'previous': 'Plays the previous song in the queue.',
        '99': 'Random quotes from Brooklyn 99.',
        'role': 'Shows your role in this server.',
        'roles': 'Shows all users and their roles.',
        'add': 'Adds two numbers together.',
        'multiply': 'Multiplies two numbers.',
    }

    message = "**Here are the available commands:**\n"
    for name, description in commands.items():
        message += f"- **{name}**: *{description}*\n"

    await ctx.send(message)

cooldowns = defaultdict(int)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Hier können Sie eine Liste von verbotenen Wörtern definieren
    banned_words = ['spam', 'spasst', 'huan', 'spasst', 'neger', 'nigga', 'nibba', 'jud', 'gay', 'ok', 'mutterficker', 'hurensohn', 'messge', 'faggot', 'midget', 'arsch', 'jude']

    # Überprüfen Sie, ob die Nachricht eines der verbotenen Wörter enthält
    for word in banned_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f'{message.author.mention}, bitte unterlasse das Verwenden von unangemessenen Wörtern!')
            return

    # Überwachen Sie die Anzahl der Nachrichten, die ein Benutzer in kurzer Zeit sendet
    user_id = message.author.id
    cooldowns[user_id] += 1
    await sleep(5)
    cooldowns[user_id] -= 1

    # Wenn ein Benutzer zu viele Nachrichten sendet, wird er für 20 Sekunden stummgeschaltet
    if cooldowns[user_id] >= 5:
        await message.channel.set_permissions(message.author, send_messages=False)
        await message.channel.send(f'{message.author.mention}, du wurdest für 20 Sekunden stummgeschaltet, weil du zu schnell geschrieben hast.')
        await sleep(20)
        await message.channel.set_permissions(message.author, overwrite=None)

    await bot.process_commands(message)


@bot.command(name="ban")
@commands.has_permissions(administrator = True)
async def ban (ctx, member:discord.User=None, reason =None):
    if member == None or member == ctx.message.author:
        await ctx.channel.send("Du kannst dich selbst nicht bannen!")
        return
    if reason == None:
        reason = "Eifach so"
    message = f"Du {ctx.guild.name} wurdest gebannt wegen: {reason}"
    await member.send(message)
    await ctx.guild.ban(member, reason=reason)
    await ctx.channel.send(f"{member} wurde gebannt!")


@bot.command(name="unban")
async def unban(ctx, *, member_name):
    banned_users = []
    async for ban_entry in ctx.guild.bans():
        banned_users.append(ban_entry)
    
    for ban_entry in banned_users:
        user = ban_entry.user

        if user.name == member_name:
            await ctx.guild.unban(user)
            await ctx.send(f'{user.name} ist wieder entbannt!')
            return

    await ctx.send(f'Kein Benutzer gefunden mit dem Namen: {member_name}')


@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel  # Bestimme den Standardkanal des Servers
    if channel is not None:
        await channel.send(f"Willkommen {member.mention} auf dem Server!")  # Sende eine Begrüßungsnachricht


brooklyn_99_quotes = [
            'I\'m the human form of the 💯 emoji.',
            'Bingpot!',
            'Cool. Cool cool cool cool cool cool cool, no doubt no doubt no doubt no doubt.',
            'Terry loves yogurt.',
            'Title of your sex tape.',
            'I\'ve made a huge mistake.',
            'Noice!',
            'Toit!',
            'Sarge, with all due respect, I am gonna completely ignore everything you just said.',
            'I\'m not a doctor, but I think it might be lupus.',
            'I asked them if they wanted to embarrass you, and they instantly said yes.',
            'I\'m playing Kwazy Cupcakes, I\'m hydrated as hell, and I\'m listening to Sheryl Crow. I\'ve got my own party going on.',
            'The only thing I\'ve ever successfully made in the kitchen is a mess.',
            'I\'m an amazing detective slash genius.',
            'If I die, turn my tweets into a book.',
            'Never not stop stopping.',
            'I\'d say I outdid myself, but I\'m always this good. So I simply did myself.',
            'I\'m not a smart man, per se, but I do know what love is.',
            'I\'m the ultimate human/genius.',
            'Yogurt is amazing! It’s the fro-yo of cheeses!'
]

@bot.command(name="99")
async def ninenine(ctx):
    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)

@bot.command(name="hallo")
async def hallo(ctx):
    user = ctx.author
    await ctx.send(f"Hallo {user.mention}!")

@bot.command(name="role")
async def role(ctx, member: discord.Member=None):
    if member is None:
        await ctx.send("Bitte gib einen Benutzernamen an!")
        return
    
    roles = member.roles
    role_names = [role.name for role in roles]
    await ctx.send(f"The roles of {member.mention} are: {', '.join(role_names)}")

@bot.command(name="roles")
async def roles(ctx):
    guild = ctx.guild
    members = guild.members

    for member in members:
        roles = member.roles
        role_names = [role.name for role in roles]
        roles_str = ", ".join(role_names)
        await ctx.send(f"**{member.name}**: {roles_str}")

#################youtube


queue = deque()
history = deque()

@bot.command(name='play')
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send(f"{ctx.message.author.mention} You are not connected to a voice channel!")
        return

    channel = ctx.message.author.voice.channel

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        voice_client = await channel.connect()

    ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}


    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        title = info['title']

    queue.append((url2, title))
    await ctx.send(f"Added {title} to the queue.")

    if not voice_client.is_playing():
        play_next(ctx, voice_client)

def play_next(ctx, voice_client):
    if len(queue) > 0:
        url2, title = queue.popleft()
        history.append((url2, title))
        voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=url2, options=['-loglevel', 'debug']), after=lambda e: play_next(ctx, voice_client))
    else:
        ctx.bot.loop.create_task(voice_client.disconnect())

@bot.command(name='queue')
async def show_queue(ctx):
    if len(queue) > 0:
        message = "Current queue:\n"
        for i, (url, title) in enumerate(queue):
            message += f"{i+1}. {title}\n"
        await ctx.send(message)
    else:
        await ctx.send("The queue is currently empty.")


@bot.command(name='stop')
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Playback stopped and disconnected from the voice channel.")
    else:
        await ctx.send("Not connected to a voice channel.")

@bot.command(name='pause')
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Playback paused.")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command(name='resume')
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("Nothing is currently paused.")

@bot.command(name='next')
async def next(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send("Skipping to the next song in the queue.")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command(name='previous')
async def previous(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if len(history) > 1:
        history.pop()
        prev_url = history.pop()
        queue.appendleft(prev_url)
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await ctx.send("Playing the previous song.")
    else:
        await ctx.send("No previous song to play.")


#################math

@bot.command(name="add")
async def add(ctx, a: str, b: str):
    a = a.replace(",", ".")
    b = b.replace(",", ".")
    
    try:
        a = float(a)
        b = float(b)
        result = perform_addition(a, b)
        await ctx.send(f"Das Ergebnis der Addition von {a} und {b} ist {result}.")
    except ValueError:
        await ctx.send("Bitte geben Sie Dezimalzahlen mit einem Punkt an.")

def perform_addition(a: float, b: float) -> float:
    return a + b


@bot.command(name="multiply")
async def multiply(ctx, a: str, b: str):
    a = a.replace(",", ".")
    b = b.replace(",", ".")
    
    try:
        a = float(a)
        b = float(b)
        result = perform_multiplication(a, b)
        await ctx.send(f"Das Ergebnis der Multiplikation von {a} und {b} ist {result}.")
    except ValueError:
        await ctx.send("Bitte geben Sie Dezimalzahlen mit einem Punkt an.")

def perform_multiplication(a: float, b: float) -> float:
    return a * b



bot.run(TOKEN)
