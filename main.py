"""HumphreyBot 0.9999999, github.com/crocash-dev"""
import os
import random
import logging
import re
import time
from datetime import datetime
import asyncio
from collections import defaultdict
import aiohttp
import matplotlib.pyplot as plt
import discord

from pytz import timezone
import pytz
from discord.ext import commands

from dotenv import load_dotenv

import wikipediaapi
import cyrtranslit
from ddgs import DDGS

# testing and debugging.
# Debug const: if False, do not load data on boot, for quick
LOAD_DATA = True
BOT_USERNAMES = ("MCbot#9631", "humphrey-bot#5757")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='humphrey.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# DATA COLLECTION
recent_message_lengths = []
user_message_count = defaultdict(int)
commands_message_count = defaultdict(int)

ROLES = [
    "blue",
    "light-cornflower-blue",
    "red",
    "dark-red",
    "pink",
    "light-pink",
    "mexican-pink",
    "purple",
    "dark-purple",
    "green",
    "bright-green",
    "dark-green",
    "chartreuse",
    "orange",
    "yellow",
    "dark-grey",
]

my_commands = [
    "!help",
    "!list_commands",
    "!list_cyr_codes",
    "!list_colours",
    "!pick_colour",
    "!echo",
    "!cyr_echo",
    "!leet_echo",
    "!fun_echo",
    "!length",
    "!quote_rinpoche",
    "!search",
    "!wiki",
    "!yt",
    "!img",
    "!meme",
    "!quote_public",
    "!len_histogram",
    "!len_line",
    "!chat_pie",
    "!command_pie",
    "!command_bar",
    "!sober",
    "!sober_totals",
    "!timezones",
    "!find_time"
]


rinpoche_quotes = [
    "All that we are looking for in life - all the happiness, contentment, and peace of mind - is right here in the present moment.",
    "Ultimately, happiness comes down to choosing between the discomfort of becoming aware of your mental afflictions and the discomfort of being ruled by them.",
    "If you're determined to think of yourself as limited, fearful, vulnerable, or scarred by past experience, know only that you have chosen to do so. The opportunity to experience yourself differently is always available.",
    "If we could see the whole truth of any situation, our only response would be one of compassion.",
    "All that we are looking for in life — all the happiness, contentment, and peace of mind — is right here in the present moment. Our very own awareness is itself fundamentally pure and good. The only problem is that we get so caught up in the ups and downs of life that we don’t take the time to pause and notice what we already have.",
    "Meditation is really quite simple. All we have to do is embrace each experience with awareness and open our hearts fully to the present moment. When we are completely at ease with our own being, the ripples of awareness naturally spread out in all directions, touching the lives of everyone we meet.",
    "The mind is the source of all experience, and by changing the direction of the mind, we can change the quality of everything we experience.",
    "There's no difference between what is seen and the mind that sees it.",
    "Compassion is the spontaneous wisdom of the heart. It's always with us. It always has been, and always will be. When it arises in us, we've simply learned to see how strong and safe we really are.",
    "Any daily activity can be used as an opportunity for meditation.",
    "Being human means having power; specifically, the power to accomplish whatever we want.",
    "It’s so easy to think that we’re the only ones who suffer, while other people are somehow immune to pain, as though they’d been born with some kind of special knowledge about being happy, that, through some cosmic accident, we never received. Thinking in this way, we make our own problems seem much bigger than they really are."
]

# latin_to_cyrillic lookalike for fun_echo
latin_to_cyrillic = str.maketrans({
    # Lowercase
    "a": "д",
    "b": "ь",
    "c": "с",
    "d": "ԁ",
    "e": "ё",
    "f": "ғ",
    "g": "ɡ",
    "h": "н",
    "i": "і",
    "j": "ј",
    "k": "к",
    "l": "ӏ",
    "m": "м",
    "n": "п",
    "o": "ф",
    "p": "р",
    "q": "ԛ",
    "r": "г",
    "s": "ѕ",
    "t": "т",
    "u": "ц",
    "v": "ѵ",
    "w": "ш",
    "x": "х",
    "y": "у",
    "z": "ᴢ",

    # Uppercase
    "A": "Д",
    "B": "В",
    "C": "С",
    "D": "Ԁ",
    "E": "Ё",
    "F": "Ғ",
    "G": "Ԍ",
    "H": "Н",
    "I": "І",
    "J": "Ј",
    "K": "К",
    "L": "Ӏ",
    "M": "М",
    "N": "П",
    "O": "Ф",
    "P": "Р",
    "Q": "ԛ",
    "R": "Г",
    "S": "Ѕ",
    "T": "Т",
    "U": "Ц",
    "V": "Ѵ",
    "W": "Ш",
    "X": "Х",
    "Y": "У",
    "Z": "ᴢ",
})

leet_map = str.maketrans({
    "A": "4", "B": "8", "C": "(", "D": "|)", "E": "3",
    "F": "ph", "G": "6", "H": "#", "I": "1", "J": "_/",
    "K": "|<", "L": "1", "M": "|\\/|", "N": "|\\|",
    "O": "0", "P": "|>", "Q": "0_", "R": "12",
    "S": "5", "T": "7", "U": "|_|", "V": "\\/",
    "W": "\\/\\/", "X": "><", "Y": "¥", "Z": "2",

    "a": "4", "b": "8", "c": "(", "d": "|)", "e": "3",
    "f": "ph", "g": "6", "h": "#", "i": "1", "j": "_/",
    "k": "|<", "l": "1", "m": '|\\/|', "n": "|\\|",
    "o": "0", "p": "|>", "q": "0_", "r": "12",
    "s": "5", "t": "7", "u": "|_|", "v": "\\/",
    "w": "\\/\\/", "x": "><", "y": "¥", "z": "2",
})


@bot.event
async def on_ready():
    """On ready"""
    if LOAD_DATA:
        for guild in bot.guilds:
            for channel in guild.text_channels:
                try:
                    async for message in channel.history(limit=1000):
                        if str(message.author) in BOT_USERNAMES:
                            print(f"Bot: {message.author} skipped")
                            continue
                        # Recent message length data collection
                        recent_message_lengths.append(len(message.content))
                        print(f"Message: {message} length {len(message.content)} recorded.")
                        # User message number data collection
                        user_message_count[str(message.author)] += 1
                        print(f"User: {str(message.author)} count: {user_message_count[str(message.author)]}")
                        # Command usage data collection
                        first_word = message.content.split(" ")[0]
                        if first_word in my_commands:
                            command = first_word
                            commands_message_count[command] += 1
                            print(f"Command: {command} incremented.")
                except discord.Forbidden:
                    print(f"No access to #{channel.name}")
    print(f"on_ready: recent_message_lengths: {recent_message_lengths}")
    print("on_ready: user_message_count:")
    print(user_message_count)
    print("on_ready: commands_message_count")
    print(commands_message_count)
    print(f"{bot.user.name} is ready for duty.")


# @bot.event
# async def on_member_join(member):
#     """On member join"""
#     await member.send(f"Welcome to Joe's Server, {member.name}")


bad_words = ["simian", "brutish", "brute", "falklands", "malvinas"]
INSTAGRAM_URL = re.compile(
    r"https?://(?:www\.)?instagram\.com/[^\s<>()]+",
    re.IGNORECASE
)


# in a @bot.listen to prevent commands not running
@bot.listen("on_message")
async def my_on_message(message):
    """On message"""
    # Variable for graph recordings
    global recent_message_lengths
    # Variable for insta-embedding
    matches_insta_link = INSTAGRAM_URL.findall(message.content)
    # Main body of function
    if message.author == bot.user:
        return
    if str(message.author) in BOT_USERNAMES:
        return
    if any((word in message.content.lower()) for word in bad_words):
        await message.channel.send(
            f"You know {message.author.name}, it is better that everyone get along.")
    # Embed insta-links
    # if matches_insta_link:
    #     fixed_links = []
    #     for url in matches_insta_link:
    #         # Preserve the path while changing the hostname
    #         fixed_url = re.sub(
    #             r"https?://(?:www\.)?instagram\.com",
    #             "https://www.hhinstagram.com",
    #             url,
    #             flags=re.IGNORECASE
    #         )
    #         fixed_url = fixed_url.split("?")[0]
    #         fixed_links.append(fixed_url)

        # # Send the converted link
        # preamble = f"{message.author} posted: "
        # return_string = preamble + "\n".join(fixed_links)
        # await message.channel.send(return_string)

        # # Optional: delete the original message
        # await message.delete()

    # Record data for graphs
    # Command usage data collection
    first_word = message.content.split(" ")[0]
    if first_word in my_commands:
        command = first_word
        commands_message_count[command] += 1
        print(f"my_on_message: Command: {command} incremented.")

    # Recent message length data collection
    recent_message_lengths.append(len(message.content))
    print(f"Message: {message} length {len(message.content)} recorded.")
    if len(recent_message_lengths) > 50000:
        recent_message_lengths = recent_message_lengths[len(recent_message_lengths) - 10000:]
        print(f"my_on_message: recent_message_lengths sliced: length now: {len(recent_message_lengths)}")

    # User message count data collection
    user_message_count[str(message.author)] += 1
    print(f"my_on_message: User: {str(message.author)} count: {user_message_count[str(message.author)]}")


# ctx = context, an object containing the context of the command
@bot.command(description="Have Humphrey echo you!")
async def echo(ctx, *, message: str):
    """Have Humprey echo you!"""
    await ctx.send(message)


@bot.command(description="Have Humphrey echo in cyrillic!")
async def cyr_echo(ctx, country_code: str, *, message: str):
    """Have Humphrey echo in Cyrillic, usage !cyr_echo country_code message"""
    return_message = cyrtranslit.to_cyrillic(message, country_code)
    await ctx.send(return_message)


@bot.command(description="List cyrillic country codes")
async def list_cyr_codes(ctx):
    """List the cyrillic country codes."""
    supported = str(cyrtranslit.supported())
    await ctx.send(supported)


@bot.command(description="Have Humphrey echo in l33t!")
async def leet_echo(ctx, *, message: str):
    """Have Humphrey echo in l33t"""
    return_message = "```" + message.translate(leet_map) + "```"
    await ctx.send(return_message)


@bot.command(description="Have Humphrey echo in a silly way!")
async def fun_echo(ctx, *, message: str):
    """Have Humphrey echo in a fun way"""
    # Latin -> Cyrillic lookalike/approximation mapping
    username = str(ctx.author)
    fun_username = username.translate(latin_to_cyrillic) + " said".translate(latin_to_cyrillic)
    fun_string = message.translate(latin_to_cyrillic)
    return_string = fun_username + ": " + fun_string
    await ctx.message.delete()
    await ctx.send(return_string)


@bot.command(description="Let Humphrey tell you the length of your message.")
async def length(ctx):
    """Let Humprey tell you the length of your message."""
    await ctx.send(f"Your message was {len(ctx.message.content) - 8} characters long.")


@bot.command(description="Recent message length histogram")
async def len_histogram(ctx):
    """Have Humphrey produce a histogram of recent message char lengths."""
    x_max = 101
    bin_interval = 5
    #plt.figure(figsize=(10, 6))
    plt.hist(
        recent_message_lengths,
        bins=range(0, x_max, bin_interval),  # 0–50, 50–100, ..., 950–1000
        edgecolor="black"
    )

    plt.title("Recent Message Lengths")
    plt.xlabel("Message Character Length")
    plt.ylabel("Number of Messages")
    plt.xlim(0, x_max - 1)
    plt.xticks(range(0, x_max, bin_interval))
    plt.tight_layout()
    plt.savefig("message_length_histogram.png")
    plt.close()

    with open("message_length_histogram.png", "rb") as f:
        await ctx.send(file=discord.File(f, "message_length_histogram.png"))


@bot.command(description="Message lengths as a line chart!")
async def len_line(ctx):
    """Have Humphrey produce a line chart of recent message lengths."""
    lengths = list(recent_message_lengths)[-100:]

    if not lengths:
        await ctx.send("There are no recent message lengths to plot.")
        return

    figure, axis = plt.subplots()

    x_axis = range(1, len(lengths) + 1)
    axis.plot(x_axis, lengths, marker="o")

    axis.set_title("Recent Message Lengths")
    axis.set_xlabel("Message (100 = newest)")
    axis.set_ylabel("Characters")
    axis.set_ylim(0, max(100, max(lengths) + 10))
    axis.grid(True)

    figure.savefig("message_length_line_chart.png")
    plt.close(figure)

    with open("message_length_line_chart.png", "rb") as f:
        await ctx.send(file=discord.File(f, filename="message_length_line_chart.png"))


@bot.command(description="User message count pie chart.")
async def chat_pie(ctx):
    """Have Humphrey produce a pie chart of user message counts!"""
    if not user_message_count:
        await ctx.send("I couldn't find any messages to chart.")
        return
    user_message_count_copy = user_message_count.copy()
    print("user_message_count_copy:")
    print(user_message_count_copy)
    bots = user_message_count_copy["MCbot#9631"] + user_message_count_copy["humphrey-bot#5757"]
    one_percent = 0.01 * (sum(user_message_count_copy.values()) - bots)
    others_sum = 0
    users_to_remove = []

    for user in user_message_count_copy:
        print("user iteration")
        if user in ("MCbot#9631", "humphrey-bot#5757"):
            users_to_remove.append(user)
        if user_message_count_copy[user] < one_percent:
            print("if < 1% entered")
            others_sum += user_message_count_copy[user]
            users_to_remove.append(user)
            print(f"{user} appended. others_sum: {others_sum}")

    print("Users to remove:")
    print(users_to_remove)
    
    for user in users_to_remove:
        if user in user_message_count_copy:
            del user_message_count_copy[user]
            print(f"del op: {user} deleted")
    print("DEL OPS COMPLETED --------------------------------------------")
    user_message_count_copy["others"] = others_sum

    users = list(user_message_count_copy.keys())
    counts = list(user_message_count_copy.values())

    plt.pie(
        counts,
        labels=users,
        # autopct="%1.1f%%", # shows percentages if enabled
        startangle=90
    )

    plt.title("Messages by User")
    plt.axis("equal")
    plt.savefig("user_message_count_pie_chart.png")
    plt.close()

    with open("user_message_count_pie_chart.png", "rb") as f:
        await ctx.send(file=discord.File(f, "user_message_count_pie_chart.png"))


@bot.command(description="Most used commands pie chart.")
async def command_pie(ctx):
    """Have Humphrey produce a pie chart of which commands are being used!"""
    if not commands_message_count:
        await ctx.send("I couldn't find any messages to chart.")
        return
    commands_message_count_copy = commands_message_count.copy()
    print("commands_message_count_copy:")
    print(commands_message_count_copy)
    
    # Sum and remove commands < 5% of total usage
    humphrey_commands = list(commands_message_count_copy.keys())
    counts = list(commands_message_count_copy.values())
    five_percent = 0.025 * sum(counts)
    others_sum = 0
    commands_to_remove = []
    for command in commands_message_count_copy:
        if commands_message_count_copy[command] < five_percent:
            others_sum += commands_message_count_copy[command]
            commands_to_remove.append(command)

    for command in commands_to_remove:
        del commands_message_count_copy[command]

    commands_message_count_copy["others"] = others_sum

    # Prepare to turn into pie chart
    humphrey_commands = list(commands_message_count_copy.keys())
    counts = list(commands_message_count_copy.values())
        
    plt.pie(
        counts,
        labels=humphrey_commands,
        # autopct="%1.1f%%", # shows percentages if enabled
        startangle=90
    )

    plt.title("Command Usage")
    plt.axis("equal")
    plt.savefig("commands_message_count_pie_chart.png")
    plt.close()

    with open("commands_message_count_pie_chart.png", "rb") as f:
        await ctx.send(file=discord.File(f, "commands_message_count_pie_chart.png"))




@bot.command(description="Most used commands bar chart.")
async def command_bar(ctx):
    """Have Humphrey produce a bar chart of which commands are being used!"""
    if not commands_message_count:
        await ctx.send("I couldn't find any messages to chart.")
        return
    commands_message_count_copy = commands_message_count.copy()
    print("commands_message_count_copy:")
    print(commands_message_count_copy)

    # Prepare to turn into bar chart
    humphrey_commands = list(commands_message_count_copy.keys())
    counts = list(commands_message_count_copy.values())
    # Make bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(
        humphrey_commands,
        counts,
    )

    fig.subplots_adjust(left=0.2, right=0.95)

    plt.title("Command Usage")
    plt.ylabel("Commands")
    plt.xlabel("Number of Times Used")
    # plt.axis("equal")
    plt.savefig("commands_message_count_bar_chart.png")
    plt.close()

    with open("commands_message_count_bar_chart.png", "rb") as f:
        await ctx.send(file=discord.File(f, "commands_message_count_bar_chart.png"))


@bot.command(description="Have Humphrey list the commands he responds to.")
async def list_commands(ctx):
    """Have Humprey list the commands."""
    message = "Try these commands, or !help <command>: "
    for command in my_commands:
        message = message + "\n" + command
    await ctx.send(message)


@bot.command(description="Have Humphrey quote the wise and compassionate Yongey Mingyur Rinpoche.")
async def quote_rinpoche(ctx):
    """Have Humphrey quote the wise Yongey Mingyur Rinpoche"""
    await ctx.send(f"```{random.choice(rinpoche_quotes)}```")


# Wikipedia searching

wiki_obj = wikipediaapi.Wikipedia(
    user_agent="HumphreyBot (github.com/crocash-dev)",
    language="en"
)


def fetch_wikipedia_page(title: str):
    """Runs synchronously in a worker thread."""
    page = wiki_obj.page(title)

    if not page.exists():
        return None

    return {
        "title": page.title,
        "summary": page.summary,
        "url": page.fullurl,
    }


@bot.command(description="Have Humphrey search Wikipedia for you!")
async def wiki(ctx, *, search: str):
    """Have Humphrey search Wikipedia."""

    try:
        result = await asyncio.to_thread(fetch_wikipedia_page, search)
    except Exception:
        await ctx.send("Wikipedia could not be reached. Please try again later.")
        return

    if result is None:
        await ctx.send(f"No Wikipedia page was found for `{search}`.")
        return

    summary = result["summary"]

    # Discord messages have a 2,000-character limit.
    if len(summary) > 1_500:
        summary = summary[:1_500].rsplit(" ", 1)[0] + "..."

    embed = discord.Embed(
        title=result["title"],
        url=result["url"],
        description=summary,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Source: Wikipedia")

    await ctx.send(embed=embed)


# Youtube Searching

@bot.command(description="Have Humphrey find a result for your Youtube Search and post it!")
async def yt(ctx, *, query: str):
    """Have Humphrey search YouTube and get a random video result."""

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "order": "relevance",
        "key": os.getenv("YOUTUBE_API_KEY"),
    }

    url = "https://www.googleapis.com/youtube/v3/search"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                error_text = await response.text()
                await ctx.send("YouTube search failed.")
                print(error_text)
                return

            data = await response.json()

    results = data.get("items", [])

    if not results:
        await ctx.send("No YouTube videos found.")
        return

    video = random.choice(results)
    video_id = video["id"]["videoId"]

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    await ctx.send(video_url)


@bot.command(description="Pick a colour role!")
async def pick_colour(ctx, *, colour: str):
    """Have Humphrey give your name a different colour!"""
    if colour not in ROLES:
        await ctx.send("That's not a valid colour role!")
        return
    for role in ctx.author.roles:
        if str(role) in ROLES:
            await ctx.author.remove_roles(role)
            print(f"{ctx.author.name} had {str(role)} removed.")
    assigning_role = discord.utils.get(ctx.guild.roles, name=colour)
    if assigning_role:
        await ctx.author.add_roles(assigning_role)
        await ctx.send(f"{ctx.author.mention} is now {assigning_role}")


@bot.command(description="List colour roles to pick from.")
async def list_colours(ctx):
    """Have Humphrey list the colour roles to pick from."""
    await ctx.send(ROLES)


# DDGS search functions

# DDGS object for use in functions
ddgs = DDGS()


# Img search
@bot.command(description="Search DuckDuckGo for an image!")
async def img(ctx, *, query: str):
    """Have Humphrey find you an image!"""
    results = ddgs.images(query=query, safesearch="moderate", max_results=50)
    # converted to list to see if empty
    if not results:
        await ctx.send("I am sorry, no urls were found.")
        return
    urls = []
    for result in results:
        urls.append(result["image"])
    print(urls)
    rand_url = random.choice(urls)
    print(rand_url)
    await ctx.send(str(rand_url))


# Text search
@bot.command(description="Search DuckDuckGo!")
async def search(ctx, *, query: str):
    """Have Humphrey search the web!"""
    results = ddgs.text(query=query, max_results=50)
    if not results:
        await ctx.send("I am sorry, no urls were found.")
        return
    print(results)
    prelim_result = random.choice(results)
    return_value = prelim_result['href']
    await ctx.send(return_value)


# Random meme

@bot.command(description="Take a random meme from #memes")
async def meme(ctx):
    """Have Humphrey post a meme from #memes"""
    print("Command !meme triggered.")
    channel = bot.get_channel(1540777913757081730)
    print("Channel:")
    print(channel)
    if channel is None:
        await ctx.send("I couldn't find the memes channel.")
        return

    messages = []

    async for message in channel.history(limit=1000):
        # Include messages with uploaded files.
        if message.attachments:
            messages.append(message)
            continue

        # Include messages whose URLs created an image preview.
        has_image_preview = False

        for embed in message.embeds:
            if embed.image.url or embed.thumbnail.url:
                has_image_preview = True
                break

        if has_image_preview:
            messages.append(message)

    print("Messages:")
    print(messages)

    if not messages:
        await ctx.send("There are no messages in the memes channel.")
        return

    random_message = random.choice(messages)
    print("Random message:")
    print(random_message)
    print("Random message content:")
    print(random_message.content)

    if random_message.attachments:
        await ctx.send(random_message.attachments[0].url)
        return

    for embed in random_message.embeds:
        if embed.image.url:
            await ctx.send(embed.image.url)
            return

        if embed.thumbnail.url:
            await ctx.send(embed.thumbnail.url)
            return


@bot.command(description="Have Humphrey quote public channel!")
async def quote_public(ctx):
    """Have Humphrey quote a post from public from #memes"""
    print("Command !quote_public triggered.")
    channel = bot.get_channel(1539717166381793372)
    print("Channel:")
    print(channel)
    if channel is None:
        await ctx.send("I couldn't find the memes channel.")
        return

    messages = []

    async for message in channel.history(limit=500):
        # Include messages with uploaded files.
        messages.append(message)

    print("Messages:")
    print(messages)

    if not messages:
        await ctx.send("There are no messages in the memes channel.")
        return

    random_message = random.choice(messages)
    print("Random message:")
    print(random_message)
    print("Random message content:")
    print(random_message.content)

    if random_message.attachments:
        await ctx.send(random_message.attachments[0].url)
        return

    for embed in random_message.embeds:
        if embed.image.url:
            await ctx.send(embed.image.url)
            return

        if embed.thumbnail.url:
            await ctx.send(embed.thumbnail.url)
            return
    return_string = "```" + random_message.content + "```"
    await ctx.send(return_string)


@bot.command(description="moo")
async def moo(ctx):
    """Moo!"""
    moo_cow = r"""
         (__)
         (oo)
   /------\/
  / |    ||
 *  /\---/\
    ~~   ~~
..."Have you mooed today?"...
"""

    await ctx.send(f"```{moo_cow}```")


@bot.command(description="Have Humphrey tell you totals of time units since Joe got dunk.")
async def sober_totals(ctx):
    now = time.time()
    difference = now - 1790759144

    minutes_sober = round(difference / 60)
    hours_sober = round(minutes_sober / 60)
    remaining_minutes = round(minutes_sober % 60)
    if remaining_minutes == 60:
        remaining_minutes = 0
    days = round(hours_sober / 24, 2)
    if days < 0:
        days = 0
    weeks = round(days / 7)
    if weeks < 0:
        weeks = 0
    months = round(weeks / 4)
    years = round(months / 12)
    return_string = fr"""Joe has been sober for totals of:
    ```
    .---------------------------.
      UNIT      |    TOTAL
    .---------------------------.
      Years     |    {years}
      Months    |    {months}
      Weeks     |    {weeks}
      Days      |    {days}
      Hours     |    {hours_sober}
      Minutes   |    {minutes_sober}
    .---------------------------.```"""
    await ctx.send(return_string)


@bot.command(description="Have Humphrey tell you how long Joe has been sober.")
async def sober(ctx):
    """Have Humphrey tell you how long Joe has been sober."""
    # Calculation of seconds since sober
    epoch_time_last_drunk = 1790759144
    now = time.time()
    difference = now - epoch_time_last_drunk
    
    total_minutes = difference / 60
    total_hours = round(total_minutes // 60)
    minutes = round(total_minutes % 60)
    total_days = round(total_hours // 24)
    hours = round(total_hours % 24)
    total_weeks = round(total_days // 7)
    days = round(total_days % 7)
    total_months = round(total_weeks // 4)
    weeks = round(total_weeks % 4)
    total_years = round(total_months // 12)
    months = round(total_months % 12)
    
    return_string = f"Joe has been sober for: {total_years} years, {months} months, {weeks} weeks, {days} days, {hours} hours and {minutes} minutes."
    await ctx.send(return_string)


# Timezone functions

def list_timezones():
    timezone_list = []
    for tz in pytz.all_timezones:
        print(tz)
        timezone_list.append(tz)
    return timezone_list


@bot.command(description="Have Humphrey list useable timezones for !find_time command")
async def timezones(ctx):
    """Have Humphrey list useable timezones for !find_time command"""
    await ctx.send("https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568")


@bot.command(description="Find the time right now in any of the timezones listed by !timezones.")
async def find_time(ctx, *, zone: str):
    """Find the time right now in any of the timezones listed by !timezones."""
    timezone_list = list_timezones()
    print(f"!find_time: {timezone_list}")
    if zone not in timezone_list:
        await ctx.send("That's not a valid timezone, I'm afraid.")
        return
    utc_now = datetime.now(pytz.utc)
    chosen_tz = timezone(zone)
    converted_time = utc_now.astimezone(chosen_tz)
    await ctx.send(converted_time)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
