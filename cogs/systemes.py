import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio

# --- Constantes d'ID ---
ROLE_FR = 1381246908932161669
ROLE_EN = 1381246992675770379
ROLE_TEMP = 1381246686738776234
PING_CHANNEL = 1381115963029585920

# Salons cibles
SALON_REGLE = 1381100094748622919
SALON_LANGUE = 1381115892477464666
SALON_VGAME = 1381115963029585920
SALON_RANK = 1381247554129236039
SALON_DYNAMI = 1381615980182245396

# Rôles
ROLE_RECRUIT = 1381109216835797072
ROLE_INEXPERIENCED = 1381109345286095000
ROLE_ROOKIE = 1381109396515459202
ROLE_VETERAN = 1381109887857201182
ROLE_TRYHARD = 1381110108154626131
ROLE_SELECTION_RANK = 1381243253332119672
RANK_OPTIONS = {
    "1-5": ROLE_RECRUIT,
    "6-10": ROLE_INEXPERIENCED,
    "11-15": ROLE_ROOKIE,
    "16-20": ROLE_VETERAN,
    "21+": ROLE_TRYHARD
}
ROLE_CRACK = 1381115255035527198
ROLE_LEGIT = 1381115472195354774
ROLE_SELECT_VGAME = 1381242962528309258
ROLE_PARTIEL = 1381243253332119672
PING_VGAME = 1381247554129236039

pending_choices = {}

# --- VIEWS ---

class LangueSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Français 🇫🇷", style=discord.ButtonStyle.primary, custom_id="lang_fr")
    async def fr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, ROLE_FR)

    @discord.ui.button(label="English 🇬🇧", style=discord.ButtonStyle.secondary, custom_id="lang_en")
    async def en_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, ROLE_EN)

    async def assign_role(self, interaction: discord.Interaction, role_id: int):
        user = interaction.user
        guild = interaction.guild
        role = guild.get_role(role_id)
        temp = guild.get_role(ROLE_TEMP)
        role_select_vgame = guild.get_role(ROLE_SELECT_VGAME)
        if role: 
            try: await user.add_roles(role)
            except discord.Forbidden:
                await interaction.response.send_message("Je n'ai pas la permission d'ajouter ce rôle.", ephemeral=True)
                return
        if role_select_vgame and role_select_vgame not in user.roles:
            try: await user.add_roles(role_select_vgame)
            except discord.Forbidden: pass
        if temp and temp in user.roles:
            try: await user.remove_roles(temp)
            except discord.Forbidden: pass
        channel = guild.get_channel(PING_CHANNEL)
        if channel:
            try:
                ping_msg = await channel.send(f"{user.mention}")
                await ping_msg.delete(delay=1)
            except Exception as e:
                print(f"Erreur ping : {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Ok, https://discordapp.com/channels/1381099938225852436/1381115963029585920", ephemeral=True
            )

class VGameChoice(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔓 Crack", style=discord.ButtonStyle.danger, custom_id="vgame_crack")
    async def crack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, ROLE_CRACK)

    @discord.ui.button(label="🔒 Légit", style=discord.ButtonStyle.success, custom_id="vgame_legit")
    async def legit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, ROLE_LEGIT)

    async def handle_choice(self, interaction: discord.Interaction, role_id: int):
        user = interaction.user
        guild = interaction.guild
        role = guild.get_role(role_id)
        if role:
            try: await user.add_roles(role)
            except discord.Forbidden:
                await interaction.response.send_message("Je n'ai pas la permission d'ajouter ce rôle.", ephemeral=True)
                return
        role_select = guild.get_role(ROLE_SELECT_VGAME)
        if role_select and role_select in user.roles:
            try: await user.remove_roles(role_select)
            except discord.Forbidden: pass
        role_partiel = guild.get_role(ROLE_PARTIEL)
        if role_partiel:
            try: await user.add_roles(role_partiel)
            except discord.Forbidden: pass
        ping_channel = guild.get_channel(PING_VGAME)
        if ping_channel:
            try:
                ping_msg = await ping_channel.send(f"{user.mention}")
                await ping_msg.delete(delay=1)
            except Exception as e:
                print(f"Erreur ping VGame : {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Ok, https://discordapp.com/channels/1381099938225852436/1381247554129236039", ephemeral=True
            )

class VGameGate(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Afficher | Show", style=discord.ButtonStyle.primary, custom_id="vgame_gate")
    async def show_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        fr_role = guild.get_role(ROLE_FR)
        en_role = guild.get_role(ROLE_EN)
        is_fr = fr_role in user.roles if fr_role else False
        is_en = en_role in user.roles if en_role else False
        if is_fr:
            desc = "Quelle est ta version du jeu ?"
        elif is_en:
            desc = "What's your game version?"
        else:
            desc = "Sélectionne ta langue d’abord."
        embed = discord.Embed(
            title="Version du jeu",
            description=desc,
            color=discord.Color.dark_green()
        )
        await interaction.response.send_message(embed=embed, view=VGameChoice(), ephemeral=True)

class RankSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Niveau 1–5", value="1-5", description="Débutant"),
            discord.SelectOption(label="Niveau 6–10", value="6-10", description="Novice"),
            discord.SelectOption(label="Niveau 11–15", value="11-15", description="Solide"),
            discord.SelectOption(label="Niveau 16–20", value="16-20", description="Confirmé"),
            discord.SelectOption(label="Niveau 21+", value="21+", description="Tryhard confirmé"),
        ]
        super().__init__(placeholder="Choisis ta tranche de niveau", options=options, custom_id="rank_select")

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if user.id in pending_choices:
            await interaction.response.send_message("Tu as déjà une sélection en attente. Confirme ou annule d’abord.", ephemeral=True)
            return
        choice = self.values[0]
        pending_choices[user.id] = choice
        fr = discord.utils.get(user.roles, id=ROLE_FR)
        en = discord.utils.get(user.roles, id=ROLE_EN)
        if fr:
            desc = f"Tu as choisi la tranche de niveau : **{choice}**.\nConfirme pour recevoir ton rôle."
        elif en:
            desc = f"You selected level range: **{choice}**.\nConfirm to receive your role."
        else:
            desc = f"Choix : **{choice}**. Confirme ou annule."
        embed = discord.Embed(title="Confirmation", description=desc, color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, view=ConfirmRank(), ephemeral=True)

class ConfirmRank(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
    @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.success, custom_id="rank_confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        choice = pending_choices.pop(user.id, None)
        if not choice:
            await interaction.response.send_message("Aucune sélection en attente.", ephemeral=True)
            return
        role_id = RANK_OPTIONS.get(choice)
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try: await user.add_roles(role)
                except discord.Forbidden:
                    await interaction.response.send_message("Je n'ai pas la permission d'ajouter ce rôle.", ephemeral=True)
                    return
        select_rank = guild.get_role(ROLE_SELECTION_RANK)
        if select_rank and select_rank in user.roles:
            try: await user.remove_roles(select_rank)
            except discord.Forbidden: pass
        final_role = guild.get_role(1381108674449117234)
        if final_role:
            try: await user.add_roles(final_role)
            except discord.Forbidden: pass
        verif_role = guild.get_role(1381241425219551334)
        if verif_role and verif_role in user.roles:
            try: await user.remove_roles(verif_role)
            except discord.Forbidden: pass
        if not interaction.response.is_done():
            await interaction.response.edit_message(content="✅", embed=None, view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger, custom_id="rank_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user.id in pending_choices:
            pending_choices.pop(user.id)
        if not interaction.response.is_done():
            await interaction.response.edit_message(content="❌ Choix annulé.", embed=None, view=None)

class RankGate(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Afficher | Show", style=discord.ButtonStyle.primary, custom_id="rank_show")
    async def show_rank_selector(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        fr = discord.utils.get(user.roles, id=ROLE_FR)
        en = discord.utils.get(user.roles, id=ROLE_EN)
        if fr:
            title = "Quel est ton niveau sur Black Ops II ?"
            desc = "Choisis ta tranche de niveau via le menu déroulant ci-dessous."
        elif en:
            title = "What's your level on Black Ops II?"
            desc = "Select your level range using the dropdown below."
        else:
            title = "Niveau"
            desc = "Sélectionne ta langue d’abord."
        embed = discord.Embed(title=title, description=desc, color=discord.Color.blurple())
        view = discord.ui.View(timeout=None)
        view.add_item(RankSelect())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ReglementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="English version", style=discord.ButtonStyle.secondary, custom_id="regle_english")
    async def english_version(self, interaction: discord.Interaction, button: discord.ui.Button):
        icon_url = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        embed = discord.Embed(
            title="📜 Server Rules",
            description="""
**I. Mutual Respect**
- Treat others the way you'd like to be treated. No toxic behavior, harassment, or gratuitous insults outside of humor.
- Hate speech, conspiracy theories, religious proclamations, personal issues — not here.

**II. No inappropriate content**
- Anything NSFW, shocking, hateful or illegal is not welcome. Keep the trafficking in-game.

**III. No spam, ads or flood**
- Ads (outside dedicated channels) are not allowed.

**IV. Respect channel themes**
- Every channel has its purpose, check before posting.
- Most have descriptions — read them. Tickets are there if anything’s unclear.

**V. Staff has the final say**
- Staff decisions are final. Don’t throw insults or hate. Got an issue? Use a ticket to reach Admins.

**VI. Profile**
- Explicit profile = risk of being quarantined on the server.
            
**VII.** : don't be idiot
            """,
            color=0x1e1f22
        )
        embed.set_footer(text="The Staff BO2 FR", icon_url=icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DynamiRoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.roles_ids = [1381111113793667092, 1381115349977530409]
        self.add_item(DynamiButton(label=" ", emoji="➕", custom_id="add_dynamic"))

class DynamiButton(Button):
    def __init__(self, label, emoji, custom_id):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary, custom_id=custom_id)
    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild
        roles = [guild.get_role(rid) for rid in [1381111113793667092, 1381115349977530409]]
        has_roles = all(role in member.roles for role in roles if role)
        if has_roles:
            view = View()
            view.add_item(Button(label="Rendre normale", style=discord.ButtonStyle.danger, custom_id="reset_dynamic"))
            view.add_item(Button(label="Laisser", style=discord.ButtonStyle.secondary, custom_id="leave_dynamic"))
            await interaction.response.send_message(
                content=(
                    "**FR 🇫🇷** : Ton profil a déjà été dynamisé, veux-tu le rendre normal ?\n"
                    "**EN 🇬🇧** : Your profile is already dynamic. Do you want to revert it?"
                ),
                ephemeral=True,
                view=view
            )
        else:
            for role in roles:
                if role and role not in member.roles:
                    try: await member.add_roles(role)
                    except discord.Forbidden:
                        await interaction.response.send_message("Permission refusée pour ajouter un rôle.", ephemeral=True)
                        return
            await interaction.response.send_message(
                "**FR 🇫🇷** : Ton profil a été dynamisé.\n**EN 🇬🇧** : Your profile has been made dynamic.", ephemeral=True
            )

# --- COG PRINCIPAL ---

class Systemes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def clear_and_send(self, channel_id, embed, view):
        await asyncio.sleep(1)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"Salon {channel_id} introuvable.")
            return
        # Supprimer uniquement le dernier message du bot
        async for msg in channel.history(limit=10):
            if msg.author == self.bot.user:
                try:
                    await msg.delete()
                except Exception:
                    pass
                break
        await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(LangueSelectView())
        self.bot.add_view(VGameGate())
        self.bot.add_view(VGameChoice())
        self.bot.add_view(RankGate())
        self.bot.add_view(ReglementView())
        self.bot.add_view(DynamiRoleView())
        print("Systemes prêt. Rafraîchissement automatique des panneaux...")

        # 1. Règlement
        icon_url = None
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if guild and guild.icon:
            icon_url = guild.icon.url
        embed_regle = discord.Embed(
            title="📜 Règlement du serveur",
            description="""
**I. Respect mutuel**
- On s’adresse aux autres comme on aimerait qu’on s’adresse à nous. Aucune insulte gratuite, comportement toxique ou harcèlement ne sera toléré dans un autre cadre qu'humoristique
- Déclaration de haine, complot, proclamations religieuses, problème relationnel, c'est hors du serveur, merci.

**II. Pas de contenu déplacé**
- Tout ce qui est NSFW, choquant, haineux ou illégal nous n'en voulons pas, restons sur les trafique dans le jeu.

**III. Pas de spam, pub ou flood**
- Toute forme de publicité (hors salons concernés) est interdit sur le serveur.

**IV. Respect de thème de salon**
- Tous les salons ont un sujet propre à lui, veillez vous assurez de respecter celui-ci avant de posté un message
- La plus part d'entre eux, si ce n'est la totalité, ont une description, prend le temps de lire. En cas d'incompréhension, les tickets sont là.

**V. Le staff a le dernier mot**
- Le staff tranchera toujours les conflits, alors il est inutile d'insulté ou de proclamer de la haine, si vous avez un problème avec un membre du staff. Le haut Staff (admin') peut s'en charger, les tickets sont disponible pour ça aussi.

**VI. Profile**
- Si votre profile affiche du contenu explicite, votre compte risque de passé en quarantaine dans le serveur.

**VII.** : Ne soit pas idiot
            """,
            color=0x1e1f22
        )
        embed_regle.set_footer(text="Le Staff BO2 FR", icon_url=icon_url)
        await self.clear_and_send(SALON_REGLE, embed_regle, ReglementView())

        # 2. Langue
        embed_langue = discord.Embed(
            title="🌐 Choisissez votre langue | Which language do you speak?",
            description="Veuillez sélectionner votre langue pour continuer :",
            color=discord.Color.blurple()
        )
        await self.clear_and_send(SALON_LANGUE, embed_langue, LangueSelectView())

        # 3. VGame
        embed_vgame = discord.Embed(
            title="Crack OU legit ?",
            description="Clique pour continuer. Nous acceptons sans soucis les cracks :D",
            color=discord.Color.greyple()
        )
        await self.clear_and_send(SALON_VGAME, embed_vgame, VGameGate())

        # 4. Rank
        embed_rank = discord.Embed(
            title="🎖️ Quel est votre niveau en jeu ? | What's your level in game",
            description="Clique pour afficher le menu.",
            color=discord.Color.dark_teal()
        )
        await self.clear_and_send(SALON_RANK, embed_rank, RankGate())

        # 5. Dynami profil
        embed_dynami = discord.Embed(
            title="Profils Dynamiques",
            description=(
                "**FR 🇫🇷** : Rendre votre profil plus dynamique en réorganisant vos rôles\n"
                "**EN 🇬🇧** : Make your profile more dynamic by reorganizing your roles"
            ),
            color=0xFF6600
        )
        await self.clear_and_send(SALON_DYNAMI, embed_dynami, DynamiRoleView())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_ids = [1381241425219551334, 1381246686738776234]
        for role_id in role_ids:
            role = member.guild.get_role(role_id)
            if role:
                try: await member.add_roles(role)
                except discord.Forbidden:
                    print(f"Pas les permissions pour ajouter {role.name} à {member}")
                except Exception as e:
                    print(f"Erreur en ajoutant {role.name} : {e}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            cid = interaction.data.get("custom_id")
            member = interaction.user
            guild = interaction.guild
            if cid == "reset_dynamic":
                for role_id in [1381111113793667092, 1381115349977530409]:
                    role = guild.get_role(role_id)
                    if role and role in member.roles:
                        try: await member.remove_roles(role)
                        except discord.Forbidden: pass
                if not interaction.response.is_done():
                    await interaction.response.edit_message(content="fait, regarde comment ton profile est plus beau :D", view=None)
            elif cid == "leave_dynamic":
                if not interaction.response.is_done():
                    await interaction.response.edit_message(content="Ok.", view=None)

async def setup(bot):
    await bot.add_cog(Systemes(bot))