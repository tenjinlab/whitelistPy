import discord
import json
from discord import mentions
from discord import guild
from discord import file
import regex as re
import pandas as pd
import os

guildTemplate = {
    'whitelist_channel': None,
    'whitelist_role': None,
    'blockchain': None,
    'data': {}
}

VALID_BLOCKCHAINS = ['eth', 'sol']


class InvalidCommand(Exception):
    def __init__(self):
        pass


class MyClient(discord.Client):
    def __init__(self, data, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.data = data
        self.commands = {
            'channel': self.set_whitelist_channel,
            'role': self.set_whitelist_role,
            'blockchain': self.set_blockchain,
            'data': self.get_data,
            'config': self.get_config
        }
        self.regex = {
            'channel': re.compile(">channel <#\d+>$"),
            'role': re.compile(">role <@&\d+>$"),
            'blockchain': re.compile(">blockchain \w{3}")
        }

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        async for guild in self.fetch_guilds():
            if str(guild.id) not in self.data.keys():
                print(f"Adding guild '{str(guild)}' to data.")
                data[str(guild.id)] = guildTemplate.copy()

    async def set_whitelist_channel(self, message: discord.Message):
        channels = message.channel_mentions
        if len(channels) != 1 or not self.regex['channel'].fullmatch(message.content):
            raise InvalidCommand()
        self.data[str(message.guild.id)]['whitelist_channel'] = channels[0].id
        await message.reply(f"Successfully set whitelist channel to <#{channels[0].id}>",
                            mention_author=True)

    async def set_whitelist_role(self, message: discord.Message) -> None:
        roles = message.role_mentions
        if len(roles) != 1 or not self.regex['role'].fullmatch(message.content):
            raise InvalidCommand()
        self.data[str(message.guild.id)]['whitelist_role'] = roles[0].id
        await message.reply(f"Successfully set whitelist role to <@&{roles[0].id}>",
                            mention_author=True)

    async def set_blockchain(self, message: discord.Message) -> None:
        code = message.content[-3:]
        if code in VALID_BLOCKCHAINS:
            self.data[str(message.guild.id)]['blockchain'] = code
            await message.reply(f"Successfully set blockchain to {code}",
                                mention_author=True)
        else:
            raise InvalidCommand()

    async def get_config(self, message: discord.Message) -> None:
        channelID = self.data[str(message.guild.id)]['whitelist_channel']
        roleID = self.data[str(message.guild.id)]['whitelist_role']
        blockchain = self.data[str(message.guild.id)]['blockchain']
        replyStr = f"Whitelist Channel: <#{channelID}>\nWhitelist Role: <@&{roleID}>\nBlockchain: {blockchain}"
        reply = discord.Embed(
            title=f'Config for {message.guild}', description=replyStr)
        await message.reply(embed=reply, mention_author=True)

    async def get_data(self, message):
        file_name = f'{message.guild.id}.csv'
        with open(file_name, 'w+') as out_file:
            out_file.write('userId, walletAddress\n')
            out_file.writelines(
                map(lambda t: f"{t[0]},{t[1]}\n", self.data[str(message.guild.id)]['data'].items()))
            out_file.flush()
        await message.reply('Data for server is attached.',
                            file=discord.File(file_name))
        os.remove(file_name)

    async def on_message(self, message):
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
                await message.reply(f"Valid commands are: {list(self.commands.keys())}")

        elif (message.channel.id == self.data[str(message.guild.id)]['whitelist_channel']
              and (self.data[str(message.guild.id)]['whitelist_role']
                   in map(lambda x: x.id, message.author.roles))):
            self.data[str(message.guild.id)]['data'][str(
                message.author.id)] = message.content
            await message.reply(
                f"Your wallet '{message.content}' has been validated and recorded.", mention_author=True)


if __name__ == '__main__':
    with open('key', 'r') as in_file:
        key = in_file.read()
    with open('data.json', 'r') as data_file:
        try:
            data = json.load(data_file)
        except json.decoder.JSONDecodeError as e:
            print(e)
            data = {}
    client = MyClient(data)
    client.run(key)
    with open('data.json', 'w') as out_file:
        json.dump(data, out_file)
