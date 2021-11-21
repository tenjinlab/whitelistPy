import discord
import json
from discord import mentions
from discord import guild
from discord import file
import regex as re
import pandas as pd
import os
from validator import *
import asyncio

GUILD_TEMPLATE = {
    'whitelist_channel': None,
    'whitelist_role': None,
    'blockchain': None,
    'data': {}
}
VALID_BLOCKCHAINS = ['eth', 'sol']


class InvalidCommand(Exception):
    """
    An exception to be thrown when an invalid command is encountered
    """

    def __init__(self):
        pass


class WhitelistClient(discord.Client):
    """
    The discord client which manages all guilds and corrosponding data
    """

    def __init__(self, data, *, loop=None, **options):
        """
        Args:
            data (dict): A data dictionary stored in memory.
        """
        super().__init__(loop=loop, **options)
        self.data = data
        self.commands = {
            'channel': self.set_whitelist_channel,
            'role': self.set_whitelist_role,
            'blockchain': self.set_blockchain,
            'data': self.get_data,
            'config': self.get_config,
            'clear': self.clear_data,
            'help': self.help
        }
        self.validators = {
            'eth': validate_eth,
            'sol': validate_sol
        }
        self.regex = {
            'channel': re.compile(">channel <#\d+>$"),
            'role': re.compile(">role <@&\d+>$"),
            'blockchain': re.compile(">blockchain \w{3}")
        }

    def backup_data(self) -> None:
        with open('data.json', 'w+') as out_file:
            json.dump(self.data, out_file)

    async def on_ready(self) -> None:
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print("Initialising...")
        async for guild in self.fetch_guilds():
            if str(guild.id) not in self.data.keys():
                print(f"Adding guild '{str(guild)}' to data.")
                data[str(guild.id)] = GUILD_TEMPLATE.copy()
        print("-------------")

    async def set_whitelist_channel(self, message: discord.Message) -> None:
        """ Handles setting the channel that will be used for whitelisting

        Args:
            message (discord.Message): The discord message containing the command request

        Raises:
            InvalidCommand: The message structure was not as expected.
        """
        channels = message.channel_mentions
        if len(channels) != 1 or not self.regex['channel'].fullmatch(message.content):
            raise InvalidCommand()
        self.data[str(message.guild.id)]['whitelist_channel'] = channels[0].id
        await message.reply(f"Successfully set whitelist channel to <#{channels[0].id}>",
                            mention_author=True)

    async def set_whitelist_role(self, message: discord.Message) -> None:
        """ Handles setting the role that will be used for whitelisting

        Args:
            message (discord.Message): The discord message containing the command request

        Raises:
            InvalidCommand: The message structure was not as expected.
        """
        roles = message.role_mentions
        if len(roles) != 1 or not self.regex['role'].fullmatch(message.content):
            raise InvalidCommand()
        self.data[str(message.guild.id)]['whitelist_role'] = roles[0].id
        await message.reply(f"Successfully set whitelist role to <@&{roles[0].id}>",
                            mention_author=True)

    async def set_blockchain(self, message: discord.Message) -> None:
        """ Handles setting the blockchain that will be used for validating wallet addresses.

        Args:
            message (discord.Message): The discord message containing the command request

        Raises:
            InvalidCommand: The message structure was not as expected.
        """
        code = message.content[-3:]
        if code in VALID_BLOCKCHAINS:
            self.data[str(message.guild.id)]['blockchain'] = code
            await message.reply(f"Successfully set blockchain to {code}",
                                mention_author=True)
        else:
            raise InvalidCommand()

    async def get_config(self, message: discord.Message) -> None:
        """ Returns the current config of a given server to the user.

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        channelID = self.data[str(message.guild.id)]['whitelist_channel']
        roleID = self.data[str(message.guild.id)]['whitelist_role']
        blockchain = self.data[str(message.guild.id)]['blockchain']
        replyStr = f"Whitelist Channel: <#{channelID}>\nWhitelist Role: <@&{roleID}>\nBlockchain: {blockchain}"
        reply = discord.Embed(
            title=f'Config for {message.guild}', description=replyStr)
        await message.reply(embed=reply, mention_author=True)

    async def get_data(self, message: discord.Message) -> None:
        """ Sends a CSV file to the user containing the current data stored by the bot

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        file_name = f'{message.guild.id}.csv'
        with open(file_name, 'w+') as out_file:
            out_file.write('userId, walletAddress\n')
            out_file.writelines(
                map(lambda t: f"{t[0]},{t[1]}\n", self.data[str(message.guild.id)]['data'].items()))
            out_file.flush()
        await message.reply('Data for server is attached.',
                            file=discord.File(file_name))
        os.remove(file_name)

    async def clear_data(self, message: discord.Message) -> None:
        """ Clears the data and config currently stored by the bot regarding the current server

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        self.data[str(message.guild.id)] = GUILD_TEMPLATE
        await message.reply("Server's data and config has been cleared.")

    async def help(self, message: discord.Message) -> None:
        """ Returns a window that provides some help messages regarding how to use the bot.

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        msg = discord.Embed(title="Whitelist Manager Help")
        desc = "Whitelist Manager is a bot designed to assist you in gathering wallet addresses for NFT drops.\nAfter configuring the discord bot, users who are 'whitelisted' will be able to record their crypto addresses which you can then download as a CSV.\nNote, the `config` must be filled out before the bot will work."
        body = "`>channel #channelName`: Sets the channel to listen for wallet addresses on.\n`>role @roleName`: Sets the role a user must possess to be able to add their address to the whitelist.\n`>blockchain eth/sol`: Select which blockchain this NFT drop will occur on, this allows for validation of the addresses that are added.\n`>config`: View the current server config.\n`>data`: Get discordID:walletAddress pairs in a CSV format.\n`>clear`: Clear the config and data for this server.\n`>help`: This screen."
        msg.description = desc
        msg.add_field(name="COMMANDS", value=body)
        await message.reply(embed=msg)

    async def on_message(self, message: discord.Message) -> None:
        """ Responds to the 'on_message' event. Runs the appropriate commands given the user has valid privellages.

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        # Handle commands
        if message.author.guild_permissions.administrator and message.content.startswith(">"):
            command = message.content.split()[0][1:]
            if command in self.commands.keys():
                try:
                    await self.commands[command](message)
                except InvalidCommand:
                    await message.reply("Invalid command argument.", mention_author=True)
            else:
                await message.reply(f"Valid commands are: `{list(self.commands.keys())}`")

        # Handle whitelist additions
        if (message.channel.id == self.data[str(message.guild.id)]['whitelist_channel']
            and (self.data[str(message.guild.id)]['whitelist_role']
                 in map(lambda x: x.id, message.author.roles))) and not message.content.startswith(">"):
            if self.validators[self.data[str(message.guild.id)]['blockchain']](message.content):
                self.data[str(message.guild.id)]['data'][str(
                    message.author.id)] = message.content
                await message.reply(
                    f"Your wallet `{message.content}` has been validated and recorded.", mention_author=True)
                self.backup_data()
            else:
                await message.reply(f"The address `{message.content}` is invalid.")


if __name__ == '__main__':
    with open('key', 'r') as in_file:
        key = in_file.read()
    try:
        with open('data.json', 'r') as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        data = {}
    client = WhitelistClient(data)
    client.run(key)
