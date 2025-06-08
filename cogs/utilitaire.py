import discord
from discord.ext import commands
from discord import app_commands, Embed, Forbidden, Member
import time
import re

class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_duration(self, duration_str):
        match = re.fullmatch(r"(\d+)(s|mn|h)", duration_str)
        if not match:
            return None
        amount, unit = match.groups()
        amount = int(amount)

        if unit == "s":
            seconds = amount
        elif unit == "mn":
            seconds = amount * 60
        elif unit == "h":
            seconds = amount * 3600
        else:
            return None

        return seconds if 0 <= seconds <= 21600 else None

    @commands.command(name="slowmode", aliases=["sm"])
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, duration: str):
        seconds = self.parse_duration(duration)
        if seconds is None:
            return await ctx.reply("Durée invalide ou au-delà de 6h. Format accepté : 10s / 5mn / 1h")

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.reply("⏱️ Mode lent désactivé dans ce canal.")
            else:
                await ctx.reply(f"⏱️ Mode lent activé : **{duration}** entre chaque message.")
        except Exception as e:
            await ctx.reply(f"Erreur : {e}")

    @commands.hybrid_command(name='mp', description="Envoie un MP à un membre")
    async def mp(self, ctx, member: discord.Member = None, *, message: str = None):
        """Envoie un MP à un membre (commande hybride)."""
        try:
            # Validation des arguments
            if not member:
                await ctx.send("Vous devez mentionner un membre pour envoyer un MP.")
                return
            if not message:
                await ctx.send("Vous devez fournir un message à envoyer.")
                return

            await member.send(message)
            await ctx.send(f"Message envoyé à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("Je ne peux pas envoyer de message à ce membre. Il a peut-être désactivé ses MP.")
        except Exception as e:
            await ctx.send(f"Une erreur est survenue : {str(e)}")

    @app_commands.command(name="envoie", description="Envoyer un message sous l'identité du bot.")
    async def say_slash(self, interaction: discord.Interaction, message: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return
        await interaction.channel.send(message)
        await interaction.response.send_message(f"✅ Message envoyé avec succès !\n'{message}'", ephemeral=True)

    # Commande préfixe +say
    @commands.command(name="envoie")
    @commands.has_permissions(manage_channels=True)
    async def say_prefix(self, ctx, *, message: str):
        await ctx.channel.send(message)
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.hybrid_command(name="supprimer", aliases=["supp"], with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def supprimer(self, ctx: commands.Context, nombre: int):
        await ctx.message.delete()  # Supprime le message de commande immédiatement.

        if nombre < 1:
            await ctx.send("Vous devez indiquer un nombre valide supérieur à 0.", delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=nombre)
        
        # Message de confirmation.
        confirmation = await ctx.send(f"🗑️ {len(deleted)} message(s) supprimé(s).")
        await confirmation.delete(delay=5)

    @commands.command(name="faituntimelessde")
    @commands.has_permissions(manage_messages=True)
    async def faituntimelessde(self, ctx, duration: str):
        """Génère un timestamp Discord et l'affiche en embed + DM au membre."""
        unit_mapping = {"s": 1, "m": 60, "h": 3600, "j": 86400}

        # Vérification de l'entrée utilisateur
        try:
            value, unit = int(duration[:-1]), duration[-1].lower()
            if unit not in unit_mapping:
                raise ValueError
        except ValueError:
            await ctx.send("**Format invalide !** Utilise : `+faituntimelessde [nombre][s/m/h/j]`")
            return

        # Calcul du timestamp
        current_time = int(time.time())
        target_time = current_time + (value * unit_mapping[unit])

        # Formatage du timestamp pour Discord
        discord_timestamp = f"<t:{target_time}:R>"

        # Envoi du message dans le salon
        embed = discord.Embed(
            title="à ton service",
            description=f"{discord_timestamp}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        # Envoi du timestamp en MP
        try:
            embed_dm = discord.Embed(
                title="Regarde",
                description=f"si tu veux utiliser le timetamp que t'as généré ({discord_timestamp}), utilise ce code :\n```\n<t:{target_time}:R>\n```",
                color=discord.Color.from_str("#ff6a00")
            )
            await ctx.author.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.send("impossible d'envoyer le timestamp en MP.")


async def setup(bot):
    await bot.add_cog(Utilitaire(bot))