import discord
import cogs.utilities.constants as consts
class AllstarCard(object):
	def __init__(self, id=None, name=None, rarity=None, attribute=None, appeal=None, stamina=None, technique=None, icon=None, art_idolized=None, idol_name=None ,name_idolized=None, icon_idolized=None, attribute_color=None, skill=[{}], passive_ability=[{}], show_ability=[{}], **kwargs):
		self.id=id
		self.name=name
		self.rarity=rarity
		self.attribute=attribute
		self.appeal=appeal
		self.stamina=stamina
		self.technique=technique
		self.icon=icon
		self.icon_idolized = icon_idolized
		self.art_idolized = art_idolized
		self.idol_name = idol_name
		self.name_idolized = name_idolized
		self.attribute_color = attribute_color
		en_skill = [x for x in skill if x.get("language","") == "en"]
		self.skill = en_skill[0] if len(en_skill) == 1 else skill[0]
		en_passive = [x for x in passive_ability if x.get("language","") == "en"]
		self.passive = en_passive[0] if len(en_passive) == 1 else passive_ability[0]
		en_active = [x for x in show_ability if x.get("language","") == "en"]
		self.active = en_active[0] if len(en_active) == 1 else show_ability[0]
		self.kwargs = kwargs

	def get_embed(self):
		skill_string = self.skill["sentence"] + "\n" + (self.skill["affects"] if self.skill.get("affects", None) else "")
		passive_string = self.passive["sentence"] + "\n" + (self.passive["affects"] if self.passive.get("affects",None) else "")
		active_string = self.active["sentence"] + "\n" + (self.active["affects"] if self.active.get("affects", None) else "")
		embed = discord.Embed(title=self.name_idolized, description=self.name, colour=discord.Colour(int(self.attribute_color.replace("#", "0x"), 16)), url=f"https://idol.st/allstars/card/{self.id}/")
		(
			embed.set_image(url=self.art_idolized)
			.set_thumbnail(url=self.icon)
			.set_author(name=self.idol_name, icon_url=consts.rarities[self.rarity])
			.add_field(name="Appeal", value=self.appeal)
			.add_field(name="Stamina", value=self.stamina)
			.add_field(name="Technique", value=self.technique)
			.add_field(name=f"Skill: { self.skill['name'].split('<br>')[0] }", value=skill_string, inline=False)
			.add_field(name=f"Passive Ability: {self.passive['name'].split('<br>')[0]}", value=passive_string, inline=False)
			.add_field(name=f"Active Ability: {self.active['name'].split('<br>')[0]}", value=active_string, inline=False)
			.set_footer(text=str(self.id))
		)
		return embed