import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(
    command_prefix="!",
    allowed_mentions=discord.AllowedMentions(
        everyone=False,
        users=True,
        roles=False
    )
)

def is_inquiry_channel():
    def predicate(ctx):
        return ctx.channel.id == int(os.environ.get('INQUIRY_CHANNEL'))
    return commands.check(predicate)

def is_inquiry_post_channel():
    def predicate(ctx):
        return ctx.channel.id == int(os.environ.get('INQUIRY_POST_CHANNEL'))
    return commands.check(predicate)

def is_public_council_channel():
    def predicate(ctx):
        return ctx.channel.id == int(os.environ.get('PUBLIC_CHANNEL'))
    return commands.check(predicate)

@bot.event
async def on_ready():
    inquiry_channel = await bot.fetch_channel(os.environ.get('INQUIRY_CHANNEL'))
    has_bot_message = False
    async for message in inquiry_channel.history():
        if message.author == bot.user:
            has_bot_message = True
            continue

        await send_to_post_channel(message)

    if not has_bot_message:
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
                "Thanks!"
            )
        )

async def send_to_post_channel(message):
    inquiry_post_channel = await bot.fetch_channel(os.environ.get('INQUIRY_POST_CHANNEL'))
    role_ping = message.guild.get_role(int(os.environ.get('ROLE_PING')))
    await inquiry_post_channel.send(f"{role_ping.mention} *New message from {message.author.mention} ({message.author.name}#{message.author.discriminator})*", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
    await inquiry_post_channel.send(content=message.content)

    for attachment in message.attachments:
        await inquiry_post_channel.send(file=await attachment.to_file())

    await inquiry_post_channel.send("------------------------------------------------------")
    await message.delete()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == int(os.environ.get('INQUIRY_CHANNEL')):
        await send_to_post_channel(message)
        return

    ctx = await bot.get_context(message)
    await bot.invoke(ctx)


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
