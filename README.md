# whitelistPy

Whitelist Manager is a discord bot designed to assist you in gathering wallet addresses for NFT drops.
After configuring the discord bot, users who are 'whitelisted' will be able to record their crypto addresses which you can then download as a CSV.
Note, the config must be filled out before the bot will work.

## COMMANDS
Note: you must be administrator to be able to access commands.

**>channel #channelName**: Sets the channel to listen for wallet addresses on.

**>role @roleName**: Sets the role a user must possess to be able to add their address to the whitelist.

**>blockchain eth/sol**: Select which blockchain this NFT drop will occur on, this allows for validation of the addresses that are added.

**>config**: View the current server config.

**>data**: Get discordID:walletAddress pairs in a CSV format.

**>clear**: Clear the config and data for this server.

**>help**: This screen.
