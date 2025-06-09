import discord
from discord.ext import commands
from discord import app_commands
import datetime
from datetime import timedelta
import asyncio
import re
import os
import json

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_duration(self, duration_str):
        match = re.fullmatch(r"(\d+)(s|mn|h|j)", duration_str)
        if not match:
            return None
        amount, unit = match.groups()
        amount = int(amount)
        if unit == "s": return timedelta(seconds=amount)
        if unit == "mn": return timedelta(minutes=amount)
        if unit == "h": return timedelta(hours=amount)
        if unit == "j": return timedelta(days=amount)
        return None

    async def _handle_mute(self, interaction_or_ctx, member: discord.Member, duration: str, reason: str):
        if member == interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author:
            return await interaction_or_ctx.response.send_message("Tu veux te faire taire toi-même ? Calmos." if isinstance(interaction_or_ctx, discord.Interaction) else "Tu veux te faire taire toi-même ? Calmos.", ephemeral=True)

        author = interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author
        guild = interaction_or_ctx.guild

        if member.top_role >= author.top_role and author != guild.owner:
            return await interaction_or_ctx.response.send_message("Pas le droit de faire taire plus haut ou égal que toi." if isinstance(interaction_or_ctx, discord.Interaction) else "Pas le droit de faire taire plus haut ou égal que toi.", ephemeral=True)

        time = self.parse_duration(duration) if duration else None
        if duration and not time:
            return await interaction_or_ctx.response.send_message("Format de durée invalide. Ex : 10s / 5mn / 2h / 1j" if isinstance(interaction_or_ctx, discord.Interaction) else "Format de durée invalide. Ex : 10s / 5mn / 2h / 1j", ephemeral=True)

        try:
            await member.timeout(time, reason=reason)
        except discord.Forbidden:
            return await interaction_or_ctx.response.send_message("J’ai pas le droit de le faire taire celui-là." if isinstance(interaction_or_ctx, discord.Interaction) else "J’ai pas le droit de le faire taire celui-là.", ephemeral=True)
        except Exception as e:
            return await interaction_or_ctx.response.send_message(f"Erreur : {e}" if isinstance(interaction_or_ctx, discord.Interaction) else f"Erreur : {e}", ephemeral=True)

        dm_embed = discord.Embed(
            title="🔇 Tu as été réduit au silence",
            description=f"Tu as été mute dans **{guild.name}**.",
            color=0xFF8000
        )
        if time:
            dm_embed.add_field(name="Durée", value=duration)
        dm_embed.add_field(name="Raison", value=reason, inline=False)
        dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=guild.icon.url if guild.icon else discord.Embed.Empty)

        try:
            await member.send(embed=dm_embed)
        except:
            pass

        msg = f"🔇 Les ondes de {member.mention} ont été brouillées."
        if time:
            msg += f" Durée : {duration}."
        msg += f"\n📝 Raison : {reason}"

        if isinstance(interaction_or_ctx, discord.Interaction):
            await interaction_or_ctx.response.send_message(msg)
        else:
            await interaction_or_ctx.reply(msg)

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute_prefix(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Aucune raison précisée"):
        await self._handle_mute(ctx, member, duration, reason)

    @app_commands.command(name="mute", description="Réduit quelqu'un au silence")
    @app_commands.describe(member="Membre à mute", duration="Durée ex: 10s/mn/h/j", reason="Raison")
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str = None, reason: str = "Aucune raison précisée"):
        await self._handle_mute(interaction, member, duration, reason)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.tree.add_command(self.mute_slash)

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "Aucune raison précisée"):
        if not member.timed_out_until:
            return await ctx.reply("Ce membre n’est pas réduit au silence.")
        
        try:
            await member.timeout(None, reason=reason)
        except discord.Forbidden:
            return await ctx.reply("J’ai pas le droit de lui rendre la parole.")
        except Exception as e:
            return await ctx.reply(f"Erreur : {e}")

        # DM Embed
        dm_embed = discord.Embed(
            title="🔊 Tu peux de nouveau parler",
            description=f"Ton mute dans **{ctx.guild.name}** a été levé.",
            color=0xFF8000
        )
        dm_embed.add_field(name="Raison", value=reason, inline=False)
        dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

        try:
            await member.send(embed=dm_embed)
        except:
            pass

        await ctx.reply(f"🔊 {member.mention} peut de nouveau s’exprimer.\n📝 Raison : {reason}")

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def slash_unmute(self, ctx, member: discord.Member, *, reason: str = "Aucune raison précisée"):
        await self.unmute(ctx, member, reason=reason)

import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Aucune raison précisée"):
        if member == ctx.author:
            return await ctx.reply("Tu veux te dégager toi-même ?")

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.reply("Pas le droit de kick plus haut ou égal que toi.")

        try:
            # MP au membre
            dm_embed = discord.Embed(
                title="👢 Tu as été éjecté",
                description=f"Tu as été kick du serveur **{ctx.guild.name}**.",
                color=0xFF8000
            )
            dm_embed.add_field(name="Raison", value=reason, inline=False)
            dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
            await member.send(embed=dm_embed)
        except:
            pass  # S'il a les MP fermés on s’en fout

        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            return await ctx.reply("J’ai pas le droit de le virer celui-là.")
        except Exception as e:
            return await ctx.reply(f"Erreur : {e}")

        await ctx.reply(f"👢 {member.mention} a été ejecté(e) de la place.\n📝 Raison : {reason}")

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def slash_kick(self, ctx, member: discord.Member, *, reason: str = "Aucune raison précisée"):
        await self.kick(ctx, member, reason=reason)

    def parse_duration(self, duration_str):
        match = re.fullmatch(r"(\d+)(s|mn|h|j)", duration_str)
        if not match:
            return None
        amount, unit = match.groups()
        amount = int(amount)
        if unit == "s": return timedelta(seconds=amount)
        if unit == "mn": return timedelta(minutes=amount)
        if unit == "h": return timedelta(hours=amount)
        if unit == "j": return timedelta(days=amount)
        return None

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Aucune raison précisée"):
        if member == ctx.author:
            return await ctx.reply("Tu veux t'autoban ? Prends un thé, respire.")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.reply("Pas le droit de ban plus haut ou égal que toi.")

        time = self.parse_duration(duration) if duration else None
        if duration and not time:
            return await ctx.reply("Format de durée invalide. Ex : 10s / 5mn / 2h / 1j")

        # MP avant le ban
        try:
            dm_embed = discord.Embed(
                title="🔨 Tu as été banni",
                description=f"Tu as été banni de **{ctx.guild.name}**.",
                color=0xFF4500
            )
            if time:
                dm_embed.add_field(name="Durée", value=duration)
            dm_embed.add_field(name="Raison", value=reason, inline=False)
            dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
            await member.send(embed=dm_embed)
        except:
            pass

        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            return await ctx.reply("Impossible de le ban. Il m'échappe.")
        except Exception as e:
            return await ctx.reply(f"Erreur : {e}")

        await ctx.reply(f"🔨 {member.mention} a été banni.\n📝 Raison : {reason}" + (f"\n⏱ Durée : {duration}" if time else ""))

        # Unban auto si durée
        if time:
            await asyncio.sleep(time.total_seconds())
            try:
                await ctx.guild.unban(discord.Object(id=member.id), reason="Fin de ban temporaire")
            except:
                pass

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def slash_ban(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Aucune raison précisée"):
        await self.ban(ctx, member, duration, reason=reason)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "Aucune raison précisée"):
        user = await self.bot.fetch_user(user_id)
        try:
            await ctx.guild.unban(user, reason=reason)
        except discord.NotFound:
            return await ctx.reply("Ce membre n'est pas banni.")
        except Exception as e:
            return await ctx.reply(f"Erreur : {e}")

        await ctx.reply(f"🔓 {user.mention} a été débanni.\n📝 Raison : {reason}")

    @commands.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def slash_unban(self, ctx, user_id: int, *, reason: str = "Aucune raison précisée"):
        await self.unban(ctx, user_id, reason=reason)


WARN_FILE = "warns.json"

def load_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns = load_warns()

    def add_warn(self, guild_id, user_id, reason, warner_id):
        gid = str(guild_id)
        uid = str(user_id)
        if gid not in self.warns:
            self.warns[gid] = {}
        if uid not in self.warns[gid]:
            self.warns[gid][uid] = []
        self.warns[gid][uid].append({
            "reason": reason,
            "date": datetime.datetime.utcnow().isoformat(),
            "warner": str(warner_id)
        })
        save_warns(self.warns)

    def remove_warn(self, guild_id, user_id, index):
        gid = str(guild_id)
        uid = str(user_id)
        if gid in self.warns and uid in self.warns[gid]:
            del self.warns[gid][uid][index]
            if not self.warns[gid][uid]:
                del self.warns[gid][uid]
            save_warns(self.warns)

    def reset_warns(self, guild_id, user_id):
        gid = str(guild_id)
        uid = str(user_id)
        if gid in self.warns and uid in self.warns[gid]:
            del self.warns[gid][uid]
            save_warns(self.warns)

    def get_warns(self, guild_id, user_id):
        return self.warns.get(str(guild_id), {}).get(str(user_id), [])

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_prefix(self, ctx, member: discord.Member, *, reason: str):
        self.add_warn(ctx.guild.id, member.id, reason, ctx.author.id)
        await ctx.reply(f"⚠️ {member.mention} a été averti pour : {reason}")

        embed = discord.Embed(title="⚠️ Avertissement reçu", description=f"Tu as été averti dans **{ctx.guild.name}**.", color=0xFFA500)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
        try:
            await member.send(embed=embed)
        except:
            pass

    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(member="Membre à avertir", reason="Raison de l'avertissement")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await self.warn_prefix(interaction, member, reason=reason)

    @app_commands.command(name="warns", description="Voir la liste des avertissements")
    @app_commands.describe(member="Membre à vérifier")
    async def warns(self, interaction: discord.Interaction, member: discord.Member):
        warns = self.get_warns(interaction.guild.id, member.id)
        embed = discord.Embed(title=f"📄 Liste d'avertissements de {member} ({len(warns)})", color=0xFFA500)
        for idx, w in enumerate(warns):
            warner = await self.bot.fetch_user(int(w["warner"]))
            date = datetime.datetime.fromisoformat(w["date"]).strftime("%d/%m/%Y")
            embed.add_field(name=f"{idx+1}. {date}", value=f"**Raison :** {w['reason']}\n**Par :** {warner.mention} ({warner.name} | {warner.id})", inline=False)

        view = WarnsView(self, interaction.guild.id, member.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class WarnsView(discord.ui.View):
    def __init__(self, cog, guild_id, user_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(RemoveWarnButton(self))
        self.add_item(ResetWarnsButton(self))

class RemoveWarnButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label="Retirer un warn", style=discord.ButtonStyle.primary)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        warns = self.view_ref.cog.get_warns(self.view_ref.guild_id, self.view_ref.user_id)
        if not warns:
            return await interaction.response.send_message("Aucun avertissement à retirer.", ephemeral=True)

        options = [discord.SelectOption(label=f"{datetime.datetime.fromisoformat(w['date']).strftime('%d/%m/%Y')} - {w['reason'][:50]}", value=str(i)) for i, w in enumerate(warns)]
        select = RemoveWarnSelect(self.view_ref, options)
        await interaction.response.send_message("Sélectionne un avertissement à retirer :", view=discord.ui.View(select), ephemeral=True)

class RemoveWarnSelect(discord.ui.Select):
    def __init__(self, view, options):
        super().__init__(placeholder="Choisir un avertissement à retirer", options=options)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        self.view_ref.cog.remove_warn(self.view_ref.guild_id, self.view_ref.user_id, index)
        await interaction.response.edit_message(content=f"✅ Warn retiré.", view=None)

class ResetWarnsButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label="Reset les warns", style=discord.ButtonStyle.danger)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        confirm = ConfirmReset(self.view_ref)
        await interaction.response.send_message("Tu confirmes la réinitialisation des warns ?", view=discord.ui.View(confirm), ephemeral=True)

class ConfirmReset(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label="Confirmer reset", style=discord.ButtonStyle.danger)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.cog.reset_warns(self.view_ref.guild_id, self.view_ref.user_id)
        await interaction.response.edit_message(content=f"🧹 Tous les warns ont été reset.", view=None)

async def setup(bot):
    await bot.add_cog(Moderation(bot))