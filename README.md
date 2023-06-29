<a href="https://discord.gg/8rxZVWdcze">
    <img src="https://img.shields.io/discord/681882711945641997?color=7289DA&label=Join our server&logo=discord&style=for-the-badge" alt="Discord">
</a>

# Coding-Bot-v6

> The sixth version of the beloved Coding Bot

## What is Coding-Bot-v6

Coding-Bot-v6 is a community bot designed to assist and support programmers within our coding community. It is the sixth version of our bot and offers advanced features and enhancements. The bot provides code-related help, suggestions, snippets, and fun.


## Commands

| Special Permissions | Category | Name (prefixes) | Description | Usage |
| --------- | --------- | --------- | --------- | --------- | 
| Owner Only | Developer | **Sync** | Sync all the slash commands globally | `{prefix}sync` |
| Owner Only | Developer | **load** | Load a Cog. | `{prefix}load [cog]` |
| Owner Only | Developer | **unload** | Unload a Cog. | `{prefix}unload [cog]` |
| Owner Only | Developer | **reload** | Reload a Cog. | `{prefix}reload [cog]` |
| Owner Only | Developer | **loadall** | Load all Cog. | `{prefix}loadall` |
| Owner Only | Developer | **unloadall** | Unload all Cog. | `{prefix}unloadall` |
| Owner Only | Developer | **reloadall** | Reload all Cog. | `{prefix}reloadall` |
| Owner Only | Developer | **getusermetric** | Get User Metrics. | `{prefix}getusermetric [member]` |
| None | Fun | **trash** | Throw someone in the trash. | `{prefix}trash [user]` |
| None | Fun | **number** | Gets a random number. | `{prefix}number`: *will get a random number* <br> `{prefix}number [number]`: *will get the [number]* |
| None | Fun | **meme** | Gets a random meme. | `{prefix}meme`: *will get a random meme* |
| None | Fun | **joke** | Gets a random joke. | `{prefix}meme`: *will get a random joke* |
| None | Fun | **eightball** | Returns a random response. | `{prefix}eightball [question]`: *will return a random response* |
| None | Fun | **token** | Generates a random token. | `{prefix}token`: *will generate a token* |
| None | Fun | **binary** | Commands for binary | `{prefix}binary` |
| None | Fun | **binary encode** | Encodes plaintext and return binary | `{prefix}binary [text]`: *return encoded text* |
| None | Fun | **binary decode** | Decode binary text to plaintext | `{prefix}binary [text]`: *return plaintext* |
| None | Fun | **reverse** | Reverse inputted string | `{prefix}reverse [string]`: *returns string reversed* | 
| None | Fun | **owofy** | Owofy inputted string | `{prefix}owofy [text]`: *returns owofy text* |
| None | Fun | **mock** | Mockify inputted string | `{prefix}mock [text]`: *returns mocked text* |
| None | Fun | **beerparty** | Start a beerparty 🍻!! | `{prefix}beerparty [reason]`: *start a beer party* |
| None | General | **source** (github, code) | Get the source of this bot | `{prefix}source` *will send link to my source code* <br > `{prefix}source [command]` *will send link to the source code of the command* <br> `{prefix}source [command] [subcommand]`: *will send link to the source code of the subcommand* | 
| None | General | **define** | Gets deinitions from Urban Dictionary. | `{prefix}define [word]`: *will send the definition of the word* |
| None | General | **avatar** | Commands for getting avatars. | `{prefix}avatar`: *will send a list of available methods* |
| None | General | **avatar main** | Start a beerparty 🍻!! | `{prefix}avatar main [user]`: *will send the main avatar of the user* |
| None | General | **avatar display** | Start a beerparty 🍻!! | `{prefix}avatar display [user]`: *will send the display avatar of the user* |
| Helpers Only | Helper | **helper** | Help command for helpers to manage the help channels | `{prefix}helper`: *will send a list of available commands* |
| Helpers Only | Helper | **helper warn** | Warns a member breaking rules in help channels | `{prefix}helper [member] [reason]`: *will give the member a warning for x reason* |
| Helpers Only | Helper | **helper warnings** | Shows a list of help warnings for a member. | `{prefix}helper warnings[<member]`: *will give a list of warnings of the member* |
| Helpers Only | Helper | **helper clearwarnings** | Clears a help warning from a member. | `{prefix}helper clearwarning [member] [index]`: *will give the member a warning for x reason* |
| Helpers Only | Helper | **helper ban** | Ban a member from help channels | `{prefix}helper [member] [reason]`: *will ban from help channels for x reason* |
| Helpers Only | Helper | **helper unban** | Unban a member from help channels | `{prefix}helper [member]`: *will unban from help channels* |
| Helpers Only | Helper | **helper verify** | Help verify a member for help channels | `{prefix}verify [member]`: *will verify a member for help channels if the member can't be verified* |
| None | Miscellaneous | **retry** (re) | Reinvoke a command | `{prefix}retry`: *will retry a commandy by replying to a message* |
| None | Miscellaneous | **afk** (afk-set, set-afk) | Set your afk status | `{prefix}afk [reason]`: *will set your afk status to [reason]* |
| None | Miscellaneous | **run** | Run code in a codeblock | `{prefix}run [code]`: *will return the result of your code* |
| None | Miscellaneous | **thank** | Thank someone | `{prefix}thank [member] [reason]`: *will thank [member] for [reason]* |
| Limited to some roles | Miscellaneous | **thank show** | Show the thanks information of a user. | `{prefix}thank show [user]`: *will show the thanks information of user* |
| Limited to some roles | Miscellaneous | **thank delete** | Delete a thank. | `{prefix}thank delete [thank_id]` : *will delete the thank with the id [thank_id]* |
| None | Miscellaneous | **thank leaderboard** (lb) | Show the thanks leaderboard. | `{prefix}thank leaderboard`: *will show the thanks leaderboard* |
| None | Miscellaneous | **trainee** | Sends the trainee help menu. | `{prefix}trainee`: *will show the trainee help menu* |
| None | Miscellaneous | **trainee list** | Lists all the trainees in the server. | `{prefix}list trainees`: *will list all the trainees in the server* |
| None | Miscellaneous | **spotify** (sp) | Shows the spotify status of a member. | `{prefix}spotify`: *will show your spotify status* <br> `{prefix}spotify [member]`: *will show the spotify status of [member]* |
| Trainee or Higher role | Moderation | **kick** | Kicks a member from the server | `{prefix}kick <member> [reason]` : *will kick [member] for [reason]* |
| Trainee or Higher role | Moderation | **ban** | Bans a member from the server | `{prefix}ban <member> [reason]` : *will ban [member] for [reason]* |
| Trainee or Higher role | Moderation | **unban** | Unbans a member from the server | `{prefix}unban <member>` : *will unban [member]* |
| Trainee or Higher role | Moderation | **mute** | Timeouts a member from the server. | `{prefix}mute <member> <duration> [reason]` : *will timeout [member] for <duration> because [reason]* |
| Trainee or Higher role | Moderation | **unmute** | Unmutes/removes timeout of a member from the server. | `{prefix}mute <member> [reason]` : *will remove timeout for [member] because [reason]* |
| Trainee or Higher role | Moderation | **massban** | Mass bans multiple users from the server | `{prefix}massban <user1> <user2> <user3> ...` : *will ban all users inputted* |
| Trainee or Higher role | Moderation | **warn** | Warn a member from the server | `{prefix}warn <member> [reason]` : *will warn [member] for [reason]* |
| Trainee or Higher role | Moderation | **Purge** | Purges a number of messages from the current channel | `{prefix}purge [amount]` : *will delete [amount] message from current channel* |
| Trainee or Higher role | Moderation | **warnings** | Lists all warnings of a member | `{prefix}warnings <member>` : *will show all warnings for [member]* |
| Trainee or Higher role | Moderation | **clearwarnings** | Clears a certain warning of a member. If no index is provided, it will clear all warnings of a member. | `{prefix}clearwarning [member] [index]` : *will clear a warning or all warnings for [member]* |
| Trainee or Higher role | Moderation | **verify** | Verifies a member in the server | `{prefix}verify <member>` : *will verify [member]* |
| Trainee or Higher role | Moderation | **verify** | Verifies a member in the server | `{prefix}verify <member>` : *will verify [member]* |
| None | Moderation | **whois** | Give information about a member | `{prefix}whois [member]` : *will give info about [member]* |
| Has permission (manage_messages) | Moderation | **delete** | Delete a message. Either the message ID can be provided or user can reply to the message. | `{prefix}delete [channel] [message]` : *will delete [message] from [channel]* |
| Has permission (manage_messages) | Moderation | **slowmode** (sm) | Sets the slowmode of a channel. | `{prefix}slowmode [seconds] [channel]` : *will set slowmode to [seconds] in [channel]* |
| Has permission (administrator) | Moderation | **lockdown** | Lock down the server, requires administrator permissions. | `{prefix}lockdown` : *will lockdown whole server (RAID ONLY)* |
| None | Moderation | **welcomer** | Welcome commands | `{prefix}welcomer` : *will show welcomer commands* |
| None | Moderation | **welcomer enable** | Enable welcomer | `{prefix}welcomer enable` : *will enable welcomer* |
| None | Moderation | **welcomer disable** | Disable welcomer | `{prefix}welcomer disable` : *will disable welcomer* |
| None | Moderation | **welcomer redirect** | Change welcome channel | `{prefix}welcomer redirect [channel]` : *will change welcomer channel to [channel]* |
| Has permission (manage_messages) | Moderation | **raid-mode** | Raid mode commands | `{prefix}raid-mode` : *will show raid mode commands* |
| Has permission (manage_messages) | Moderation | **raid-mode enable** | Enable raid mode | `{prefix}raid-mode enable` : *will enable raid mode* |
| Has permission (manage_messages) | Moderation | **raid-mode disable** | Disable raid mode | `{prefix}raid-mode disable` : *will disable raid mode* |



## Self-Hosting: 
### Requirements
* [Python 3.10+](https://www.python.org/downloads/)
* [Modules in requirements.txt](https://github.com/The-Coding-Realm/coding-bot-v6/blob/master/requirements.txt)

### Quick Start
```sh
git clone https://github.com/The-Coding-Realm/coding-bot-v6.git  #Clone the repository
cd coding-bot-v6                   #Go to the directory
python -m pip install -r requirements.txt   #Install required packages
```

### Configuration
1. Rename .env.example to .env
2. Replace the empty space with your token:
```
TOKEN = your_token.here
```


After installing all packages and configuring your bot, start your bot by running `python main.py`


## Contribution
Coding Bot V6 is an open sourced discord bot, and we are looking more contributors to improve its code. Please check the wiki section reagarding to [How to Contribute](https://github.com/The-Coding-Realm/coding-bot-v6/wiki/How-To-Contribute)<a href="https://discord.gg/8rxZVWdcze">
