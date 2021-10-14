import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import random

load_dotenv()

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

bot = commands.Bot(
    command_prefix="!",
    allowed_mentions=discord.AllowedMentions(
        everyone=False,
        users=True,
        roles=False
    ),
    intents=discord.Intents.all()
)

def is_public_council_channel():
    def predicate(ctx):
        return ctx.channel.id == int(os.environ.get('PUBLIC_CHANNEL'))
    return commands.check(predicate)

class OpenCouncilThread(discord.ui.View):
    @discord.ui.button(label="Open New Inquiry", style=discord.ButtonStyle.blurple, emoji="📬", custom_id="councilbot:open_new_inquiry",)
    async def openthread(self, button: discord.ui.Button, interaction: discord.Interaction):
        if "PRIVATE_THREADS" not in interaction.channel.guild.features:
            raise Exception("Private threads must be available on this server")

        if "SEVEN_DAY_THREAD_ARCHIVE" in interaction.channel.guild.features:
            duration=7*24*60
        elif "THREE_DAY_THREAD_ARCHIVE" in interaction.channel.guild.features:
            duration=3*24*60
        else:
            duration=24*60

        thread: discord.Thread = await interaction.channel.create_thread(name=f"Inquiry {interaction.user.name} {random.randint(0,999)}", message=None, auto_archive_duration=duration)
        await thread.add_user(interaction.user)
        await interaction.response.send_message(f"A new thread called {thread.mention} has been opened for this inquiry.", ephemeral=True)
        role_ping = interaction.channel.guild.get_role(int(os.environ.get('ROLE_PING')))
        for member in role_ping.members:
            logging.info(f"Adding {member.name}#{member.discriminator} to thread {thread.name}")
            await thread.add_user(member)
        logging.info(f"Adding {interaction.user.name}#{interaction.user.discriminator} to thread {thread.name}")

@bot.event
async def on_ready():
    inquiry_channel = await bot.fetch_channel(os.environ.get('INQUIRY_CHANNEL'))
    async for message in inquiry_channel.history():
        if message.author == bot.user:
            await message.delete()
            continue

    await inquiry_channel.send(
        content=(
            "**__Council Inquiry Channel__**\n\n"
            "This channel exists so you may submit an inquiry to the ALTTPR Racing Council for consideration.\n\n"
            "Examples of inquiries may be:\n"
            "1) Requests to clarify the rules of competitive play.\n"
            "2) Requests for glitch classification for use in competitive play.\n"
            "3) Suspected cheating or other skulduggery (do not supply specifics, just request a follow up via DM).\n"
            "4) Any other business that you think should be taken up by the council.\n\n"
            "What should you **not** use this channel for?\n"
            "1) Memes or jokes.\n"
            "2) Messages to harass members of the racing council\n"
            "3) Non racing-related issues, such as randomizer development, casual multiworlding, etc.\n\n"
            "These messages go to real humans (believe it or not) and abuse will result in a loss of access to this channel, and other council-related channels.\n\n"
            "To **submit an inquiry**, click the 📬 button below to get started!\n\n"
            "Thanks!"
        ),
        view=OpenCouncilThread()
    )

# @bot.event
# async def on_message(message: discord.Message):
#     if int(os.environ.get("INQUIRY_CHANNEL")) == message.channel.id:
#         if not message.author == bot.user:
#             thread = await create_inquiry_thread(message.channel, message.author)
#             await thread.send(f"Message from {message.author.mention}")
#             await thread.send(message.content)
#             try:
#                 await message.author.send(f"A new thread called {thread.mention} has been opened for this inquiry.")
#             except Exception:
#                 logging.exception(f"Unable to send DM to user {message.author.name}#{message.author.discriminator}.")
#             await message.delete()

@bot.event
async def on_command_error(ctx, error):
    await ctx.message.remove_reaction('⌚', ctx.bot.user)
    if isinstance(error, (commands.errors.CheckFailure)):
        return
    elif isinstance(error, commands.CommandNotFound):
        return
    await ctx.message.add_reaction("❌")
    await ctx.reply(f"```{error}```")
    raise error

# async def create_inquiry_thread(channel: discord.TextChannel, user: discord.Member, interaction) -> discord.Thread:


@bot.event
async def on_command(ctx):
    await ctx.message.add_reaction('⌚')


@bot.event
async def on_command_completion(ctx):
    await ctx.message.add_reaction('✅')
    await ctx.message.remove_reaction('⌚', ctx.bot.user)

@bot.command()
@is_public_council_channel()
@commands.check_any(commands.has_any_role('Council Members', 'Admins', 'Mods'), commands.is_owner(), commands.has_permissions(manage_permissions=True))
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.reply("This channel is now locked.")

@bot.command()
@is_public_council_channel()
@commands.check_any(commands.has_any_role('Council Members', 'Admins', 'Mods'), commands.is_owner(), commands.has_permissions(manage_permissions=True))
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.reply("This channel is now unlocked.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(os.environ.get("DISCORD_TOKEN")))
    loop.run_forever()
