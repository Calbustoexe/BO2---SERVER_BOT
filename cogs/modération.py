import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
from datetime import timedelta
import asyncio
import re
import os
import json

WARN_FILE = "warns.json"
TEMPBAN_FILE = "tempbans.json"

def load_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_tempbans():
    if not os.path.exists(TEMPBAN_FILE):
        return {}
    with open(TEMPBAN_FILE, "r") as f:
        # Convert datetime strings back to datetime objects
        raw = json.load(f)
        bans = {}
        for gid, users in raw.items():
            bans[int(gid)] = {}
            for uid, until in users.items():
                bans[int(gid)][int(uid)] = datetime.datetime.fromisoformat(until)
        return bans

def save_tempbans(temp_bans):
    data = {}
    for gid, users in temp_bans.items():
        data[str(gid)] = {str(uid): until.isoformat() for uid, until in users.items()}
    with open(TEMPBAN_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_duration(duration_str):
    if not duration_str:
        return None
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

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns = load_warns()
        self.temp_bans = load_tempbans()  # {guild_id: {user_id: unban_time}}
        self.check_tempbans.start()

    def cog_unload(self):
        self.check_tempbans.cancel()
        save_tempbans(self.temp_bans)

    # --- MUTE SYSTEM ---
    async def _handle_mute(self, interaction_or_ctx, member: discord.Member, duration: str, reason: str):
        author = interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author
        guild = interaction_or_ctx.guild

        if member == author:
            msg = "Tu veux te faire taire toi-même ? Calmos."
            if isinstance(interaction_or_ctx, discord.Interaction):
                return await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                return await interaction_or_ctx.reply(msg)

        if member.top_role >= author.top_role and author != guild.owner:
            msg = "Pas le droit de faire taire plus haut ou égal que toi."
            if isinstance(interaction_or_ctx, discord.Interaction):
                return await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                return await interaction_or_ctx.reply(msg)

        time = parse_duration(duration) if duration else None
        if duration and not time:
            msg = "Format de durée invalide. Ex : 10s / 5mn / 2h / 1j"
            if isinstance(interaction_or_ctx, discord.Interaction):
                return await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                return await interaction_or_ctx.reply(msg)

        try:
            await member.timeout(time, reason=reason)
        except discord.Forbidden:
            msg = "J’ai pas le droit de le faire taire celui-là."
            if isinstance(interaction_or_ctx, discord.Interaction):
                return await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                return await interaction_or_ctx.reply(msg)
        except Exception as e:
            msg = f"Erreur : {e}"
            if isinstance(interaction_or_ctx, discord.Interaction):
                return await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                return await interaction_or_ctx.reply(msg)

        # MP
        dm_embed = discord.Embed(
            title="🔇 Tu as été réduit au silence",
            description=f"Tu as été mute dans **{guild.name}**.",
            color=0xFF8000
        )
        if time:
            dm_embed.add_field(name="Durée", value=duration)
        dm_embed.add_field(name="Raison", value=reason, inline=False)
        dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=guild.icon.url if guild.icon else None)

        try:
            await member.send(embed=dm_embed)
        except Exception:
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

        dm_embed = discord.Embed(
            title="🔊 Tu peux de nouveau parler",
            description=f"Ton mute dans **{ctx.guild.name}** a été levé.",
            color=0xFF8000
        )
        dm_embed.add_field(name="Raison", value=reason, inline=False)
        dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)

        try:
            await member.send(embed=dm_embed)
        except Exception:
            pass

        await ctx.reply(f"🔊 {member.mention} peut de nouveau s’exprimer.\n📝 Raison : {reason}")

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def slash_unmute(self, ctx, member: discord.Member, *, reason: str = "Aucune raison précisée"):
        await self.unmute(ctx, member, reason=reason)

    # --- KICK SYSTEM ---
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Aucune raison précisée"):
        if member == ctx.author:
            return await ctx.reply("Tu veux te dégager toi-même ?")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.reply("Pas le droit de kick plus haut ou égal que toi.")

        # MP au membre
        try:
            dm_embed = discord.Embed(
                title="👢 Tu as été éjecté",
                description=f"Tu as été kick du serveur **{ctx.guild.name}**.",
                color=0xFF8000
            )
            dm_embed.add_field(name="Raison", value=reason, inline=False)
            dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            await member.send(embed=dm_embed)
        except Exception:
            pass

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

    # --- BAN SYSTEM ---
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Aucune raison précisée"):
        if member == ctx.author:
            return await ctx.reply("Tu veux t'autoban ? Prends un thé, respire.")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.reply("Pas le droit de ban plus haut ou égal que toi.")

        time = parse_duration(duration) if duration else None
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
            dm_embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            await member.send(embed=dm_embed)
        except Exception:
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
            until = datetime.datetime.utcnow() + time
            self.temp_bans.setdefault(ctx.guild.id, {})[member.id] = until
            save_tempbans(self.temp_bans)

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

    # --- !banf (ban le dernier à avoir parlé dans le salon) ---
    @commands.command(name="banf")
    @commands.has_permissions(ban_members=True)
    async def banf(self, ctx, duration: str = None, *, reason: str = None):
        """Bannit la dernière personne à avoir parlé dans ce salon. Ex: !banf 1j insulte"""
        await ctx.trigger_typing()
        messages = [msg async for msg in ctx.channel.history(limit=2)]  # [cmd, dernier msg]
        if len(messages) < 2:
            return await ctx.send("Impossible de trouver un message précédent dans ce salon.")
        target_msg = messages[1]
        member = ctx.guild.get_member(target_msg.author.id)
        if not member:
            return await ctx.send("Impossible de trouver ce membre sur le serveur.")
        if member == ctx.author:
            return await ctx.send("Tu ne peux pas te ban toi-même !")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("Tu ne peux pas ban un membre avec un rôle égal ou supérieur au tien.")

        delta = parse_duration(duration) if duration else None

        # MP avant ban
        try:
            guild_name = ctx.guild.name
            txt = f"Vous avez été banni du serveur **{guild_name}**"
            if duration:
                txt += f" pour une durée de **{duration}**"
            else:
                txt += " (bannissement définitif)"
            if reason:
                txt += f"\nRaison : {reason}"
            else:
                txt += "\nAucune raison n'a été spécifiée."
            txt += "\n\nSi vous pensez qu'il s'agit d'une erreur, contactez le staff."
            await member.send(txt)
        except Exception:
            pass

        try:
            await ctx.guild.ban(member, reason=reason or "Ban via !banf", delete_message_days=0)
        except discord.Forbidden:
            return await ctx.send("Je n'ai pas la permission de bannir ce membre.")
        txt = f"{member.mention} a été banni"
        if delta:
            txt += f" pour {duration}"
            until = datetime.datetime.utcnow() + delta
            self.temp_bans.setdefault(ctx.guild.id, {})[member.id] = until
            save_tempbans(self.temp_bans)
        else:
            txt += " définitivement"
        if reason:
            txt += f" | Raison : {reason}"
        await ctx.send(txt)

    # --- !banm (ban la dernière personne mentionnée dans le salon) ---
    @commands.command(name="banm")
    @commands.has_permissions(ban_members=True)
    async def banm(self, ctx, duration: str = None, *, reason: str = None):
        """Bannit la dernière personne mentionnée dans ce salon. Ex: !banm 1j insulte"""
        await ctx.trigger_typing()
        async for msg in ctx.channel.history(limit=20):
            if msg.mentions and msg.id != ctx.message.id:
                target = msg.mentions[-1]
                member = ctx.guild.get_member(target.id)
                if not member:
                    return await ctx.send("Impossible de trouver ce membre sur le serveur.")
                if member == ctx.author:
                    return await ctx.send("Tu ne peux pas te ban toi-même !")
                if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                    return await ctx.send("Tu ne peux pas ban un membre avec un rôle égal ou supérieur au tien.")
                delta = parse_duration(duration) if duration else None

                # MP avant ban
                try:
                    guild_name = ctx.guild.name
                    txt = f"Vous avez été banni du serveur **{guild_name}**"
                    if duration:
                        txt += f" pour une durée de **{duration}**"
                    else:
                        txt += " (bannissement définitif)"
                    if reason:
                        txt += f"\nRaison : {reason}"
                    else:
                        txt += "\nAucune raison n'a été spécifiée."
                    txt += "\n\nSi vous pensez qu'il s'agit d'une erreur, contactez le staff."
                    await member.send(txt)
                except Exception:
                    pass

                try:
                    await ctx.guild.ban(member, reason=reason or "Ban via !banm", delete_message_days=0)
                except discord.Forbidden:
                    return await ctx.send("Je n'ai pas la permission de bannir ce membre.")
                txt = f"{member.mention} a été banni"
                if delta:
                    txt += f" pour {duration}"
                    until = datetime.datetime.utcnow() + delta
                    self.temp_bans.setdefault(ctx.guild.id, {})[member.id] = until
                    save_tempbans(self.temp_bans)
                else:
                    txt += " définitivement"
                if reason:
                    txt += f" | Raison : {reason}"
                return await ctx.send(txt)
        await ctx.send("Aucune personne mentionnée dans les derniers messages.")

    # --- Temp Ban Unban Task ---
    @tasks.loop(seconds=10)
    async def check_tempbans(self):
        now = datetime.datetime.utcnow()
        to_unban = []
        for guild_id, d in self.temp_bans.items():
            for user_id, until in list(d.items()):
                if now >= until:
                    to_unban.append((guild_id, user_id))
        for guild_id, user_id in to_unban:
            guild = self.bot.get_guild(guild_id)
            if guild:
                try:
                    await guild.unban(discord.Object(id=user_id), reason="Ban temporaire expiré")
                except Exception:
                    pass
            self.temp_bans[guild_id].pop(user_id, None)
            save_tempbans(self.temp_bans)
        # Clean empty dicts
        for guild_id in list(self.temp_bans.keys()):
            if not self.temp_bans[guild_id]:
                del self.temp_bans[guild_id]
        save_tempbans(self.temp_bans)

    # --- WARN SYSTEM ---
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
        embed.set_footer(text="Le Staff BO2 FR", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        try:
            await member.send(embed=embed)
        except Exception:
            pass

    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(member="Membre à avertir", reason="Raison de l'avertissement")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        ctx = await self.bot.get_context(interaction)
        await self.warn_prefix(ctx, member, reason=reason)

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