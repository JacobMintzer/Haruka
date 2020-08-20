# Haruka
Discord bot for management of the Nijigasaki Discord and adjacent Love Live servers. Features include:
* Welcome messages and autoroles.
* Create custom self-assignable roles.
* Have exclusive self-assignable roles: where you can only have 1 in a set.
* Self assignable pronouns.
* Ban users (including users not in the server yet), purge messages, nuke channels.
* Lookup emotes in other servers.
* Event logging: set a channel for messags whenever a message is deleted, edited, someone joins, or leaves.
* Shuffled music in voice chat, and requesting songs to a queue.
* Activity rankings that ignores spam, and automatically assigning ranks when specified thresholds are reached. 
* Automoderation based on existing scores
* SIFAS card lookups using https://github.com/bocktagon/LLAS_API
* A subscribable newsletter for Haruka updates.
* Reverse Image searching using the SauceNao API

To invite Haruka to your server, use this link: https://discord.com/api/oauth2/authorize?client_id=613501680469803045&permissions=268774468&scope=bot
### TODO
* Scheduling (base scheduler is working, just need to implement the birthday/mutes)
  * birthday messages to users/girls
  * mutes/umutes
  * <s>$remindMe function</s>
* <s>Allow true multi-server support without breaking everything</s> (just need to do music, <s>scoring</s>, and automod)
* Youtube support, including revamping the queue system
* Specific ban system for when people inevitably abuse this system
* <s>Import and improve Maribot's antispam automoderation</s> done
* Haruka specific message when people boost
* SIF/<s>SIFAS</s> card info lookups 
* Extract image from pixiv links
