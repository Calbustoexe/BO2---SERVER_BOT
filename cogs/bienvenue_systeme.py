import discord
from discord.ext import commands

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}  # Pour garder l'état des invitations

    @commands.Cog.listener()
    async def on_ready(self):
        # On charge les invites en cache pour chaque serveur
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except Exception:
                self.invites[guild.id] = []

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Quand le bot rejoint un nouveau serveur, on initialise le cache
        try:
            self.invites[guild.id] = await guild.invites()
        except Exception:
            self.invites[guild.id] = []

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.get_channel(1381316590292832447)
        if not channel:
            return

        # Cherche l'invitation utilisée
        old_invites = self.invites.get(member.guild.id, [])
        try:
            new_invites = await member.guild.invites()
            self.invites[member.guild.id] = new_invites
        except Exception:
            new_invites = []

        inviter = None
        used_code = None

        # Compare les usages pour trouver l'invitation utilisée
        for old in old_invites:
            matching_new = next((inv for inv in new_invites if inv.code == old.code), None)
            if matching_new and matching_new.uses > old.uses:
                inviter = matching_new.inviter
                used_code = matching_new.code
                break

        # Si pas trouvé, prend la première qui a le plus d'usages (fallback)
        if inviter is None and new_invites:
            most_used = max(new_invites, key=lambda inv: inv.uses)
            if most_used.uses > 0 and most_used.inviter:
                inviter = most_used.inviter
                used_code = most_used.code

        # Construction de l'embed
        embed = discord.Embed(
            title="Bienvenue !",
            description="Le serveur te souhaite un bon séjour ici. Passe lire les règles et surtout amuse toi :D",
            color=0xe67000
        )
        # En haut à droite : membre
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        # En bas à gauche : serveur
        embed.set_footer(text=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
        # Thumbnail : logo serveur
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)

        # Ajout de l'inviteur si trouvé
        if inviter:
            embed.add_field(name="Invité par", value=f"{inviter.mention}", inline=False)
            if used_code:
                embed.add_field(name="Code d'invitation", value=used_code, inline=False)

        # Ping du membre en dehors de l'embed
        await channel.send(content=member.mention, embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))