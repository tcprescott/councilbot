import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import random

load_dotenv()

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class CouncilBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=True,
                roles=False
            ),
            intents=discord.Intents.all()
        )
        self.persistent_views_added = False

    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(OpenCouncilThread())
            self.persistent_views_added = True

        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

bot = CouncilBot()

def is_public_council_channel():
    def predicate(ctx):
        return ctx.channel.id == int(os.environ.get('PUBLIC_CHANNEL'))
    return commands.check(predicate)

class OpenCouncilThread(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open New Inquiry", style=discord.ButtonStyle.blurple, emoji="📬", custom_id="councilbot:open_inquiry")
    async def openthread(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = ConfirmCouncilThread()
        await interaction.response.send_message(
            (
                "Are you sure you want to **ping a bunch of people**?\n\n"
                "This message will stop working after one minute.\n"
                "If you did not intend to do this, simply click \"Dismiss message\" at the bottom of this response. Thanks!"
            ),
            view=view, ephemeral=True)
        pass

class ConfirmCouncilThread(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Yes!", style=discord.ButtonStyle.red, row=2)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
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

@bot.command()
@commands.is_owner()
async def inquiry(ctx):
    await ctx.send(
        content=(
            "**__Council Inquiry Channel__**\n\n"
            "This channel exists so you may submit an inquiry to the ALTTPR Racing Council for consideration.\n\n"
            "Examples of inquiries may be:\n"
            "1) Requests to clarify the rules of competitive play.\n"
            "2) Requests for glitch classification for use in competitive play.\n"
            "3) Suspected cheating or other skulduggery.\n"
            "4) Any other business that you think should be taken up by the council.\n\n"
            "What should you **not** use this channel for?\n"
            "1) Memes or jokes.\n"
            "2) Inquiries to harass members of the racing council\n"
            "3) Non racing-related issues, such as randomizer development, casual multiworlding, etc.\n\n"
            "Abuse will result in a loss of access to this channel, and other council-related channels.  This button **pings the whole council**.\n\n"
            "To **submit an inquiry**, click the 📬 button below, then click \"Yes!\" button in the next message to confirm.\n\n"
            "Thanks!"
        ),
        view=OpenCouncilThread()
    )

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
