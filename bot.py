from gc import get_objects
from pkgutil import get_data
from pydoc import describe
from sqlite3 import Timestamp
from time import time
from turtle import title
from unicodedata import name
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.abc import GuildChannel
import json
from pyowm.utils.config import get_default_config
import pyowm
from pyowm.owm import OWM

import bot_config
import nekos
import requests
import datetime
import func
import sqlite3

bad_words = ["блять", "сука", "заебал", "шлюха"]
config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM('ba449a573627e3b078e5e1cfc0e5d2d1', config_dict)
serverId = 899236044686381117
dog_api = requests.get(f'{bot_config.DOG_API}').json()

owm = pyowm.OWM('ba449a573627e3b078e5e1cfc0e5d2d1')
mgr =  owm.weather_manager()
connection = sqlite3.connect('economy.db')
cursor = connection.cursor()

def get_prefix(client, message):
    with open("jsons/prefix.json", "r") as f:
        prefix = json.load(f)

    return prefix[str(message.guild.id)]

client = commands.Bot(command_prefix=get_prefix)
client.remove_command("help")

@client.event
async def on_ready():
    print("Connected!")

    await client.change_presence( status = nextcord.Status.online, activity = nextcord.Streaming(name = "YouTube", url = "https://www.youtube.com/channel/UCAM-m8nzQCOlNVPQCBOugYg") )
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            name TEXT,
            id INT,
            cash BIGINT,
            rep INT,
            lvl INT
        )""")
    connection.commit()

    for guild in client.guilds:
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 100, 0, 1)")               
            else:
                pass
    connection.commit()

@client.event
async def on_message(message):
    await client.process_commands( message )

    msg = message.content.lower()

    if msg in bad_words:
        channel = message.channel
        await message.delete()
        await channel.send(f"{message.author.mention}, по ебалу захотел?")
        print("[log] Deleted bad word!")

@client.event
async def on_guild_join(guild):
    with open("jsons/prefix.json", "r") as f:
        prefix = json.load(f)
    prefix[str(guild.id)] = "."
    with open("jsons/prefix.json", "w") as f:
        prefix = json.dump(prefix, f, indent=4) 

@client.event
async def on_guild_remove(guild):
    with open("jsons/prefix.json", "r") as f:
        prefix = json.load(f)
    prefix.pop(str(guild.id))
    with open("jsons/prefix.json", "w") as f:
        prefix = json.dump(prefix, f, indent=4)

@client.event
async def on_member_join(member):
    if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
        cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 100, 0, 1)")
        connection.commit()
    else:
        pass 

@client.command()
async def setprefix(ctx, new: str):
    with open("jsons/prefix.json", "r") as f:
        prefix = json.load(f)
    prefix[str(ctx.guild.id)] = new
    with open("jsons/prefix.json", "w") as f:
        prefix = json.dump(prefix, f, indent=4) 
    await ctx.send(f"Новый префикс: `{new}`")

@client.slash_command(guild_ids=[serverId])
async def slashping(interaction: Interaction):
    await interaction.response.send_message("Pong!")

@client.slash_command(guild_ids=[serverId])
async def clear(interaction: Interaction, amount: int):       
    if amount > 100:
        await interaction.response.send_message("Я не могу удалять больше 100 сообщений!", ephemeral=True)
    else:
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Удалено: {amount} сообщения(ий)! :wastebasket:", ephemeral=True)

@client.slash_command(guild_ids=[serverId])
async def help(interaction: Interaction):
    emb = nextcord.Embed(title=f"Fnorex's help panel", color = nextcord.Color.GREEN)
    emb.add_field(name="/clear", value="Delete messages", inline=False)
    emb.add_field(name=".server", value="Info about server", inline=False)
    emb.add_field(name=".help", value="Help menu", inline=False)
    emb.add_field(name=".stats", value="Bot stats", inline=False)
    emb.add_field(name=".kill", value="Kill member", inline=False)
    emb.add_field(name=".ping", value="Test command", inline=False)
    emb.add_field(name="/ping", value="Test command", inline=False)
    emb.set_author(name=client.user.name, icon_url=client.user.avatar)

    await interaction.response.send_message(embed=emb)

@client.slash_command(guild_ids=[serverId])
async def weather(interaction: Interaction, city: str):
        observation =  mgr.weather_at_place( city )
        w =  observation.weather
        temp = w.temperature('celsius')["temp"]

        answer = f"В городе {city} сейчас {w.detailed_status}\n"
        answer += " Температура сейчас в районе "+ str(temp) + "\n\n"

        if temp < 10:
            answer += "Сейчас жестко холодно, кырык кабат киын" 
        elif temp < 20:
            answer += "Сейчас холодно, оденься потеплее" 
        else:
            answer += "Температура найс, одевайся как хош" 

        await interaction.response.send_message(answer, ephemeral=True)

@client.command(name="server", description="Server information")
async def server(ctx):
    role_count = len(ctx.guild.roles)
    list_of_bots = [bot.mention for bot in ctx.guild.members if bot.bot]

    emb = nextcord.Embed(timestamp = ctx.message.created_at, color = ctx.author.color)
    emb.add_field(name ="Name:", value = f"{ctx.guild.name}", inline = False)
    emb.add_field(name ="Bots:", value = f"{list_of_bots}", inline = False)
    emb.add_field(name ="Roles:", value = f"{role_count}", inline = False)

    await ctx.send( embed = emb )

@client.command(name="help" ,description="Help menu")
async def help(ctx):
    emb = nextcord.Embed(title="Fnorex's Help", description="Help menu for bot commands")
    for command in client.walk_commands():
        description = command.description
        if not description or description is None or description == "":
            description = 'No description provided'
        emb.add_field(name=f"`.{command.name}{command.signature if command.signature is not None else ''}`", value=description)
        await ctx.send(embed=emb)

@client.command(name="ping", description="Test command")
async def ping(ctx):
    await ctx.reply("Pong!")

@client.command()
async def stats(ctx):
    serverCount = len(client.guilds)
    memberCount = len(set(client.get_all_members()))
    embed = nextcord.Embed(title='Статистика', description='\uFEFF', colour=ctx.author.colour, timestamp=ctx.message.created_at)
    embed.add_field(name='Версия бота:', value='1.0')
    embed.add_field(name='Число гильдий:', value=serverCount)
    embed.add_field(name='Число всех участников:', value=memberCount)
    embed.add_field(name='Разработчик бота:', value="<@641239378814959616>")
    embed.set_footer(text=f"{ctx.message.author}")
    embed.set_author(name=client.user.name, icon_url=client.user.avatar)
    await ctx.send(embed=embed)

@client.command()
async def dog(ctx):
    emb = nextcord.Embed(title="Random Dog", colour = nextcord.Color.green())
    emb.set_author( name = client.user.name, icon_url = client.user.avatar )
    emb.set_image(url = dog_api[0]['url'])

    await ctx.send( embed = emb )

@client.command()
async def lessons(ctx):
    school_api = requests.get("https://kalininoschoolapi.herokuapp.com/api/v1/lessons/0").json()
    emb = nextcord.Embed(title="School Lessons", colour = nextcord.Color.green())
    emb.set_author( name = client.user.name, icon_url = client.user.avatar )
    emb.add_field(name = "Monday", value=f"{school_api[1]['lessons']}")

    await ctx.send( embed = emb )

@client.command()
async def cat(ctx):
    emb = nextcord.Embed(title="Random Cat", colour = nextcord.Color.green())
    emb.set_author( name = client.user.name, icon_url = client.user.avatar )
    emb.set_image(url = nekos.cat())

    await ctx.send( embed = emb )

@client.command(aliases=['cash', 'bal'])
async def balance(ctx, member: nextcord.Member = None):
    if member is None:
        await ctx.send(embed = nextcord.Embed(
                description = f"""Баланс пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :leaves:**"""
            ))
    else:
        await ctx.send(embed = nextcord.Embed(
                description = f"""Баланс пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} :leaves:**"""
            ))  

@client.command()
async def kill( ctx, member: nextcord.Member, arg ):
	if arg == 'Дробовик':
		embed = nextcord.Embed(title = 'Убийство', description = 'Вы сможете кого-то убить дробовиком', colour = nextcord.Color.red())
	elif arg == 'Нож':
		embed = nextcord.Embed(title = 'Убийство', description = 'Вы сможете кого-то убить ножом', colour = nextcord.Color.red())

	if arg == 'Дробовик':
		embed.add_field( name = '**Доставание дробовика**', value = f"{ctx.author.mention} достаёт дробовик...", inline = False )
	elif arg == 'Нож':
		embed.add_field( name = '**Доставание ножа**', value = f"{ctx.author.mention} достаёт нож...", inline = False )

	if arg == 'Дробовик':
		embed.add_field( name = '**Направление дробовика**', value = f"{ctx.author.mention} направляет дробовик на {member.mention}...", inline = False )
	elif arg == 'Нож':
		embed.add_field( name = '**Думание попадания**', value = f"{ctx.author.mention} думает, куда будет бить на {member.mention}...", inline = False )

	if arg == 'Дробовик':
		embed.add_field( name = '**Стрельба**', value = f"{ctx.author.mention} стреляет в {member.mention}...", inline = False )
	elif arg == 'Нож':
		embed.add_field( name = '**Попадание**', value = f"{ctx.author.mention} попадает ножом в {member.mention}...", inline = False )
	
	if arg == 'Дробовик':
		embed.set_image(url='https://media.discordapp.net/attachments/690222948283580435/701494203607416943/tenor_3.gif')
	elif arg == 'Нож':
		embed.set_image(url='https://cdn.discordapp.com/attachments/789452703084445727/790543128058396692/305253a407fa8da8.gif')

	embed.add_field( name = '**Кровь**', value = f"{member.mention} истекает кровью...", inline = False )


	embed.add_field( name = '**Погибание**', value = f"{member.mention} погиб...", inline = False )

	await ctx.send( embed = embed )


client.run(bot_config.TOKEN)