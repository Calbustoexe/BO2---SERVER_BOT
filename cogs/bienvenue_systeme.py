import discord
from discord.ext import commands

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.get_channel(1381316590292832447)
        if not channel:
            return

        inviter = None
        invite_data = await member.guild.invites()
        for invite in invite_data:
            if invite.uses and invite.inviter:
                inviter = invite.inviter
                break

        embed = discord.Embed(
            title=f"Bienvenue {member.name} !",
            description="Le serveur te souhaite un bon séjour ici. Passe lire les règles et surtout amuse toi :D",
            color=0xe67000
        )
        embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else discord.Embed.Empty)
        embed.set_footer(text=f"{member.name}", icon_url=member.display_avatar.url)

        if inviter:
            embed.add_field(name="\u200b", value=f"- Invité par {inviter.mention}", inline=False)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
