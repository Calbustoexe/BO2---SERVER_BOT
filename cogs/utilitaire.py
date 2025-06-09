import discord
from discord.ext import commands
from discord import app_commands, Embed, Forbidden, Interaction
import datetime
import time
import re
import json
import os
from discord.ui import Button, View
from discord import ButtonStyle
import asyncio
import random

class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # For hidden channels and logs, ensure persistence in memory
        self.hidden_channels = {}
        self.logs = {}

    # ----------- Utils ----------
    def parse_duration(self, duration_str):
        """Parse une durée en s/mn/h et retourne le nombre de secondes (max 6h)."""
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

    # ----------- Slowmode ----------
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

    # ----------- MP -----------
    @commands.hybrid_command(name='mp', description="Envoie un MP à un membre")
    async def mp(self, ctx, member: discord.Member = None, *, message: str = None):
        """Envoie un MP à un membre (commande hybride)."""
        if not member:
            await ctx.send("Vous devez mentionner un membre pour envoyer un MP.")
            return
        if not message:
            await ctx.send("Vous devez fournir un message à envoyer.")
            return
        try:
            await member.send(message)
            await ctx.send(f"Message envoyé à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("Je ne peux pas envoyer de message à ce membre. Il a peut-être désactivé ses MP.")
        except Exception as e:
            await ctx.send(f"Une erreur est survenue : {str(e)}")

    # ----------- Say (slash + prefix) -----------
    @app_commands.command(name="envoie", description="Envoyer un message sous l'identité du bot.")
    async def say_slash(self, interaction: discord.Interaction, message: str):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Vous n'avez pas la permission pour cette commande.", ephemeral=True)
            return
        await interaction.channel.send(message)
        await interaction.response.send_message(f"✅ Message envoyé avec succès !\n'{message}'", ephemeral=True)

    @commands.command(name="envoie")
    @commands.has_permissions(manage_channels=True)
    async def say_prefix(self, ctx, *, message: str):
        await ctx.channel.send(message)
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    # ----------- Purge -----------
    @commands.hybrid_command(name="supprimer", aliases=["supp"], with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def supprimer(self, ctx: commands.Context, nombre: int):
        # Supprime le message de commande immédiatement, sauf avec slash
        if hasattr(ctx, "message"):
            try:
                await ctx.message.delete()
            except Exception:
                pass

        if nombre < 1:
            await ctx.send("Vous devez indiquer un nombre valide supérieur à 0.", delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=nombre)
        try:
            confirmation = await ctx.send(f"🗑️ {len(deleted)} message(s) supprimé(s).", delete_after=5)
        except Exception:
            pass

    # ----------- Générateur de timestamp -----------
    @commands.command(name="faituntimelessde")
    @commands.has_permissions(manage_messages=True)
    async def faituntimelessde(self, ctx, duration: str):
        """Génère un timestamp Discord et l'affiche en embed + DM au membre."""
        unit_mapping = {"s": 1, "m": 60, "h": 3600, "j": 86400}
        try:
            value, unit = int(duration[:-1]), duration[-1].lower()
            if unit not in unit_mapping:
                raise ValueError
        except ValueError:
            await ctx.send("**Format invalide !** Utilise : `+faituntimelessde [nombre][s/m/h/j]`")
            return
        current_time = int(time.time())
        target_time = current_time + (value * unit_mapping[unit])
        discord_timestamp = f"<t:{target_time}:R>"
        embed = discord.Embed(
            title="à ton service",
            description=f"{discord_timestamp}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        try:
            embed_dm = discord.Embed(
                title="Regarde",
                description=f"si tu veux utiliser le timetamp que t'as généré ({discord_timestamp}), utilise ce code :\n```\n<t:{target_time}:R>\n```",
                color=discord.Color.from_str("#ff6a00")
            )
            await ctx.author.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.send("impossible d'envoyer le timestamp en MP.")

    # ----------- Hide/Unhide Channel -----------
    @commands.command(name="hide")
    @commands.has_permissions(manage_guild=True)
    async def hide(self, ctx, channel: discord.TextChannel = None):
        """Cache un salon pour tout le monde sauf les modérateurs."""
        if channel is None:
            channel = ctx.channel
        everyone_role = ctx.guild.default_role
        mod_role = ctx.guild.get_role(1145807576353742908)
        # Sauvegarde des permissions avant modification
        if channel.id not in self.hidden_channels:
            self.hidden_channels[channel.id] = {
                role.id: channel.overwrites.get(role) for role in ctx.guild.roles if role.position < mod_role.position
            }
        await channel.set_permissions(everyone_role, view_channel=False)
        for role in ctx.guild.roles:
            if role.position < mod_role.position and role != everyone_role:
                await channel.set_permissions(role, view_channel=False)
        await ctx.send(f"le salon {channel.mention} est maintenant caché.")

    @commands.command(name="unhide")
    @commands.has_permissions(manage_guild=True)
    async def unhide(self, ctx, channel: discord.TextChannel = None):
        """Rend un salon visible à nouveau en restaurant les permissions initiales."""
        if channel is None:
            channel = ctx.channel
        if channel.id not in self.hidden_channels:
            await ctx.send("déjà visible par tous")
            return
        # Restauration des permissions originales
        for role_id, overwrite in self.hidden_channels[channel.id].items():
            role = ctx.guild.get_role(role_id)
            if role:
                await channel.set_permissions(role, overwrite=overwrite)
        del self.hidden_channels[channel.id]
        await ctx.send(f"tout le monde peut à nouveau voir {channel.mention}.")

    @hide.error
    async def hide_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Tu n'as pas la permission pour cette commande**")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ **Salon introuvable**")
        else:
            await ctx.send("❌ **Oups, une erreur est survenue**")

    # ----------- Logging Events -----------
    async def log_event(self, event_type, user, target, details):
        event_data = {
            "event_type": event_type,
            "user": user.name,
            "user_id": user.id,
            "target": target.name if isinstance(target, discord.Member) else str(target),
            "target_id": str(target.id) if hasattr(target, "id") else str(target),
            "details": details,
            "timestamp": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        }
        if not hasattr(self, "logs"):
            self.logs = {}
        if event_data["target_id"] not in self.logs:
            self.logs[event_data["target_id"]] = []
        self.logs[event_data["target_id"]].append(event_data)
        with open('event_logs.json', 'w') as f:
            json.dump(self.logs, f, indent=4)

    # ----------- Message All -----------
    @commands.hybrid_command(name="message_all", description="Envoyer un message à tout le monde dans le serveur.")
    @commands.has_permissions(administrator=True)
    async def message_all(self, ctx, title: str, content: str, footer: str, color: str = "#3498db"):
        embed = self.create_embed(title, content, footer, color)
        buttons = self.create_buttons(ctx, embed)
        preview_msg = await ctx.send(
            embed=embed,
            content="**Prévisualisation** : ajustez avant l'envoi :",
            view=buttons,
            ephemeral=True
        )
        buttons.preview_msg = preview_msg
        buttons.embed = embed

    def create_embed(self, title: str, content: str, footer: str, color: str):
        try:
            embed_color = int(color.strip("#"), 16)
        except ValueError:
            embed_color = 0x3498db
        embed = discord.Embed(title=title, description=content, color=embed_color)
        embed.set_footer(text=footer)
        return embed

    def create_buttons(self, ctx, embed):
        buttons = View(timeout=300)
        confirm_button = Button(label="Confirmer", style=ButtonStyle.green)
        cancel_button = Button(label="Annuler", style=ButtonStyle.red)
        edit_button = Button(label="Modifier", style=ButtonStyle.blurple)
        color_button = Button(label="Changer la couleur", style=ButtonStyle.grey)

        async def confirm_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas confirmer cette action.", ephemeral=True)
                return
            await interaction.response.edit_message(content="📨 Début de l'envoi... Cela peut prendre du temps.", view=None)
            failed_members = await self.send_to_all_members(ctx.guild, embed)
            await ctx.send(f"✅ Message envoyé à tous les membres.\nMembres inaccessibles : {failed_members}")

        async def cancel_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas annuler cette action.", ephemeral=True)
                return
            await interaction.response.edit_message(content="❌ Envoi annulé.", view=None)

        async def edit_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas modifier ce message.", ephemeral=True)
                return
            await self.handle_edit(interaction, embed)

        async def color_callback(interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Vous ne pouvez pas modifier ce message.", ephemeral=True)
                return
            await self.handle_color_change(interaction, embed)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        edit_button.callback = edit_callback
        color_button.callback = color_callback

        buttons.add_item(confirm_button)
        buttons.add_item(cancel_button)
        buttons.add_item(edit_button)
        buttons.add_item(color_button)
        return buttons

    async def send_to_all_members(self, guild, embed):
        failed_members = []
        for member in guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed)
                    await asyncio.sleep(random.uniform(1.0, 2.5))  # Délai réduit pour éviter blocage
                except discord.Forbidden:
                    failed_members.append(str(member))
                except Exception:
                    failed_members.append(str(member))
        return len(failed_members)

    async def handle_edit(self, interaction, embed):
        await interaction.response.send_message("📝 Entrez les champs à modifier (`titre`, `contenu`, `footer`).", ephemeral=True)
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ Temps écoulé.", ephemeral=True)
            return
        fields_to_edit = msg.content.split()
        for field in fields_to_edit:
            if field == "titre":
                await interaction.followup.send("Entrez le nouveau titre :", ephemeral=True)
                title_msg = await self.bot.wait_for('message', check=check, timeout=60)
                embed.title = title_msg.content
            elif field == "contenu":
                await interaction.followup.send("Entrez le nouveau contenu :", ephemeral=True)
                content_msg = await self.bot.wait_for('message', check=check, timeout=60)
                embed.description = content_msg.content
            elif field == "footer":
                await interaction.followup.send("Entrez le nouveau footer :", ephemeral=True)
                footer_msg = await self.bot.wait_for('message', check=check, timeout=60)
                embed.set_footer(text=footer_msg.content)
        await interaction.edit_original_response(embed=embed)

    async def handle_color_change(self, interaction, embed):
        await interaction.response.send_message("🎨 Entrez une nouvelle couleur en hexadécimal.", ephemeral=True)
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        try:
            color_msg = await self.bot.wait_for('message', check=check, timeout=60)
            embed.color = int(color_msg.content.strip("#"), 16)
            await interaction.edit_original_response(embed=embed)
        except (ValueError, asyncio.TimeoutError):
            await interaction.followup.send("❌ Couleur invalide ou délai dépassé.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utilitaire(bot))