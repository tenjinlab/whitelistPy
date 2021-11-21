import discord
import json
from discord import mentions
import regex as re

guildTemplate = {
    'whitelist_channel': None,
    'whitelist_role': None,
    'data': {}
}


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
            'channel': re.compile(">channel <#\d+>$")
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
        await message.reply("Successfully set whitelist channel.",
                            mention_author=True)

    async def set_whitelist_role(self, message):
        return message

    async def set_blockchain(self, message):
        return message

    async def get_config(self, message):
        return message

    async def get_data(self, message):
        return message

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
