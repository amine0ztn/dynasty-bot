"""
============================================================
 BOT DISCORD - DYNASTY (South District RP)
============================================================
Fonctionnalités :
  1. Système de candidature (formulaire + vote Direction/RH/Manager)
  2. Modération de base (kick, mute, clear, ban)
  3. Message de bienvenue automatique à l'arrivée d'un membre

Avant de lancer ce bot, lis le fichier GUIDE_HEBERGEMENT.md
============================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime

# ============================================================
# CONFIGURATION - À MODIFIER avant de lancer le bot
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")  # Le token est lu depuis une variable d'environnement (jamais en dur dans le code)

# ID du salon où les candidatures seront envoyées (clic droit sur le salon > Copier l'identifiant)
SALON_CANDIDATURES_ID = 1520362837057474651

# ID du salon #réponses-candidatures où le bot poste le vote (Direction/RH/Managers)
SALON_VOTE_ID = 1520010526032134206

# ID du rôle "Responsable RH" — sera notifié (ping) à chaque nouvelle candidature
ROLE_RH_ID = 1520349367108763800

# ID du rôle "Directeur" — sera AUSSI notifié (ping) à chaque nouvelle candidature
ROLE_DIRECTEUR_ID = 1520349188083286137

# ID du rôle donné automatiquement quand quelqu'un postule (ex: "Postulant")
ROLE_POSTULANT_ID = 1520366535690944622

# IDs des rôles autorisés à VOTER sur les candidatures : Direction + RH + Managers
# Exemple : ROLES_VOTANTS = [111111111111111111, 222222222222222222, 333333333333333333]
ROLES_VOTANTS = [1520349188083286137, 1520349367108763800, 1520349596142796892]

# Rôles autorisés à utiliser les commandes de modération
ROLES_MODERATION = []  # <-- liste d'IDs de rôles, ex: [123456789, 987654321]

# ID du salon où le message de bienvenue sera posté quand quelqu'un rejoint le serveur
SALON_BIENVENUE_ID = 1520004684264378458

# ============================================================
# INITIALISATION DU BOT
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Connecté en tant que {bot.user} - Dynasty Bot est en ligne.")


# ============================================================
# MESSAGE DE BIENVENUE
# ============================================================

@bot.event
async def on_member_join(member: discord.Member):
    salon = member.guild.get_channel(SALON_BIENVENUE_ID)
    if salon is None:
        print("⚠️ SALON_BIENVENUE_ID n'est pas configuré ou invalide.")
        return

    embed = discord.Embed(
        title="🏢 BIENVENUE CHEZ DYNASTY 🏢",
        description=(
            "*South District RP*\n\n"
            "Bonjour et bienvenue parmi nous !\n\n"
            "**Dynasty** est l'une des entreprises les plus respectées de **South District**. "
            "Que tu sois un futur client, partenaire, ou que tu rêves de rejoindre nos équipes, "
            "tu es au bon endroit.\n\n"
            "📌 **Avant toute chose :**\n"
            "1️⃣ Lis attentivement le règlement dans `#règlement`\n"
            "2️⃣ Si tu veux nous rejoindre, utilise la commande `/postuler` pour envoyer ta candidature\n\n"
            "🤝 **Une question ?** N'hésite pas à nous contacter sur la centrale !!\n\n"
            "On est ravis de t'accueillir. Bienvenue chez **Dynasty** ! 🚪✨"
        ),
        color=discord.Color.from_rgb(0, 200, 120),
        timestamp=datetime.datetime.now(),
    )
    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Membre n°{member.guild.member_count} • {member.guild.name}")

    await salon.send(content=member.mention, embed=embed)


# ============================================================
# SYSTÈME DE CANDIDATURE
# ============================================================

class FormulaireCandidature(discord.ui.Modal, title="Candidature - Dynasty"):
    nom_prenom = discord.ui.TextInput(
        label="Nom et Prénom",
        placeholder="Ex: John Smith",
        required=True,
        max_length=50,
    )
    age = discord.ui.TextInput(
        label="Âge",
        placeholder="Ex: 27",
        required=True,
        max_length=3,
    )
    raison = discord.ui.TextInput(
        label="Pourquoi rejoindre le Dynasty ?",
        style=discord.TextStyle.paragraph,
        placeholder="Explique en quelques lignes...",
        required=True,
        max_length=500,
    )
    lettre_motivation = discord.ui.TextInput(
        label="Lettre de motivation",
        style=discord.TextStyle.paragraph,
        placeholder="Présente-toi et explique ce que tu peux apporter à Dynasty...",
        required=True,
        max_length=1000,
    )
    telephone = discord.ui.TextInput(
        label="Numéro de téléphone",
        placeholder="Ex: 06 12 34 56 78",
        required=True,
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction):
        salon = interaction.guild.get_channel(SALON_CANDIDATURES_ID)

        if salon is None:
            await interaction.response.send_message(
                "⚠️ Erreur : le salon de candidatures n'est pas configuré. Préviens un responsable.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📋 Nouvelle candidature - Dynasty",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
        embed.add_field(name="Nom et Prénom", value=self.nom_prenom.value, inline=True)
        embed.add_field(name="Âge", value=self.age.value, inline=True)
        embed.add_field(name="Pourquoi rejoindre le Dynasty ?", value=self.raison.value, inline=False)
        embed.add_field(name="Lettre de motivation", value=self.lettre_motivation.value, inline=False)
        embed.add_field(name="Numéro de téléphone", value=self.telephone.value, inline=True)
        embed.set_footer(text=f"ID utilisateur : {interaction.user.id}")

        # L'embed complet (Nom RP, Motivation...) n'est visible QUE par le candidat (ephemeral plus bas).
        # Dans #candidature, on poste juste une notification sans détail pour Direction + RH.

        # 1) Notifie Direction + RH dans #candidature, SANS afficher le détail de la candidature
        pings = " ".join(f"<@&{r}>" for r in (ROLE_RH_ID, ROLE_DIRECTEUR_ID) if r)
        await salon.send(
            content=(
                f"{pings}\n📋 Nouvelle candidature de {interaction.user.mention} reçue. "
                f"Détails envoyés en privé + vote disponible dans le salon de vote."
                if pings else
                f"📋 Nouvelle candidature de {interaction.user.mention} reçue."
            ),
        )

        # 2) Poste le VOTE complet dans #réponses-candidatures (Direction + RH + Managers)
        salon_vote = interaction.guild.get_channel(SALON_VOTE_ID)
        if salon_vote is not None:
            embed_vote = embed.copy()
            embed_vote.title = "🗳️ Vote - Candidature Dynasty"
            embed_vote.add_field(name="Statut du vote", value="⏳ En cours...", inline=False)

            view_vote = VoteCandidature(interaction.user)
            vote_msg = await salon_vote.send(embed=embed_vote, view=view_vote)
            view_vote.message = vote_msg
        else:
            print("⚠️ SALON_VOTE_ID n'est pas configuré ou invalide.")

        # Donne le rôle "Postulant" si configuré
        if ROLE_POSTULANT_ID:
            role = interaction.guild.get_role(ROLE_POSTULANT_ID)
            if role:
                try:
                    await interaction.user.add_roles(role)
                except discord.Forbidden:
                    pass

        # 3) Le candidat reçoit la confirmation + le récap de SA candidature, en privé (lui seul le voit)
        await interaction.response.send_message(
            "✅ Ta candidature a bien été envoyée à l'équipe de Dynasty ! Tu seras contacté(e) prochainement.\n"
            "Voici un récapitulatif de ce que tu as envoyé :",
            embed=embed,
            ephemeral=True,
        )


class VoteCandidature(discord.ui.View):
    """Vote ✅ / ❌ pour Direction + RH + Managers. Décision à la majorité simple."""

    def __init__(self, candidat: discord.User):
        super().__init__(timeout=None)
        self.candidat = candidat
        self.message: discord.Message | None = None
        self.votes: dict[int, bool] = {}  # user_id -> True (oui) / False (non)
        self.termine = False

    def _peut_voter(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        if not ROLES_VOTANTS:
            return True  # si pas configuré, tout le monde peut voter (à éviter, configure ROLES_VOTANTS)
        return any(role.id in ROLES_VOTANTS for role in interaction.user.roles)

    def _resume_votes(self) -> str:
        oui = sum(1 for v in self.votes.values() if v)
        non = sum(1 for v in self.votes.values() if not v)
        return f"✅ {oui} pour  •  ❌ {non} contre  ({len(self.votes)} votant(s))"

    async def _maj_embed(self, statut: str | None = None):
        embed = self.message.embeds[0]
        embed.set_field_at(len(embed.fields) - 1, name="Statut du vote", value=statut or self._resume_votes(), inline=False)
        await self.message.edit(embed=embed, view=self)

    async def _cloturer(self, accepte: bool):
        self.termine = True
        for child in self.children:
            child.disabled = True

        resultat_txt = "✅ **ACCEPTÉE**" if accepte else "❌ **REFUSÉE**"
        await self._maj_embed(f"{resultat_txt}\n{self._resume_votes()}")

        try:
            if accepte:
                await self.candidat.send(
                    "🎉 Félicitations ! Ta candidature chez **Dynasty** a été **acceptée** "
                    "suite au vote de la direction. Un responsable va te contacter pour la suite."
                )
            else:
                await self.candidat.send(
                    "❌ Ta candidature chez **Dynasty** n'a malheureusement pas été retenue "
                    "suite au vote de la direction. Tu peux retenter ta chance plus tard !"
                )
        except discord.Forbidden:
            pass

    async def _voter(self, interaction: discord.Interaction, valeur: bool):
        if self.termine:
            await interaction.response.send_message("Le vote est déjà clôturé.", ephemeral=True)
            return

        if not self._peut_voter(interaction):
            await interaction.response.send_message(
                "❌ Seuls la Direction, les RH et les Managers peuvent voter sur les candidatures.",
                ephemeral=True,
            )
            return

        self.votes[interaction.user.id] = valeur
        await self._maj_embed()
        await interaction.response.send_message(
            f"Ton vote ({'✅ pour' if valeur else '❌ contre'}) a bien été pris en compte.",
            ephemeral=True,
        )

    @discord.ui.button(label="✅ Pour", style=discord.ButtonStyle.success)
    async def pour(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._voter(interaction, True)

    @discord.ui.button(label="❌ Contre", style=discord.ButtonStyle.danger)
    async def contre(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._voter(interaction, False)

    @discord.ui.button(label="🔒 Clôturer le vote", style=discord.ButtonStyle.secondary)
    async def cloturer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._peut_voter(interaction):
            await interaction.response.send_message(
                "❌ Seuls la Direction, les RH et les Managers peuvent clôturer un vote.",
                ephemeral=True,
            )
            return

        if self.termine:
            await interaction.response.send_message("Le vote est déjà clôturé.", ephemeral=True)
            return

        if not self.votes:
            await interaction.response.send_message("Personne n'a encore voté.", ephemeral=True)
            return

        oui = sum(1 for v in self.votes.values() if v)
        non = sum(1 for v in self.votes.values() if not v)
        accepte = oui > non  # majorité simple ; égalité = refusé par défaut

        await interaction.response.defer()
        await self._cloturer(accepte)


@bot.tree.command(name="postuler", description="Envoyer une candidature pour rejoindre Dynasty")
async def postuler(interaction: discord.Interaction):
    await interaction.response.send_modal(FormulaireCandidature())


# ============================================================
# MODÉRATION DE BASE
# ============================================================

def a_la_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    if not ROLES_MODERATION:
        return interaction.user.guild_permissions.manage_messages
    return any(role.id in ROLES_MODERATION for role in interaction.user.roles)


@bot.tree.command(name="clear", description="Supprime un nombre de messages dans le salon")
@app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
async def clear(interaction: discord.Interaction, nombre: int):
    if not a_la_permission(interaction):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    nombre = max(1, min(nombre, 100))
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=nombre)
    await interaction.followup.send(f"🧹 {len(deleted)} messages supprimés.", ephemeral=True)


@bot.tree.command(name="kick", description="Exclure un membre du serveur")
@app_commands.describe(membre="Le membre à exclure", raison="Raison de l'exclusion")
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    if not a_la_permission(interaction):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    try:
        await membre.kick(reason=raison)
        await interaction.response.send_message(f"👋 {membre.mention} a été exclu. Raison : {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission d'exclure ce membre (vérifie la hiérarchie des rôles).", ephemeral=True)


@bot.tree.command(name="ban", description="Bannir un membre du serveur")
@app_commands.describe(membre="Le membre à bannir", raison="Raison du bannissement")
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    if not a_la_permission(interaction):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    try:
        await membre.ban(reason=raison)
        await interaction.response.send_message(f"🔨 {membre.mention} a été banni. Raison : {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de bannir ce membre (vérifie la hiérarchie des rôles).", ephemeral=True)


@bot.tree.command(name="mute", description="Rendre un membre muet temporairement (timeout)")
@app_commands.describe(membre="Le membre à rendre muet", minutes="Durée en minutes", raison="Raison du mute")
async def mute(interaction: discord.Interaction, membre: discord.Member, minutes: int, raison: str = "Aucune raison fournie"):
    if not a_la_permission(interaction):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    duree = datetime.timedelta(minutes=minutes)
    try:
        await membre.timeout(duree, reason=raison)
        await interaction.response.send_message(f"🔇 {membre.mention} a été rendu muet pour {minutes} minutes. Raison : {raison}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de faire ça (vérifie la hiérarchie des rôles).", ephemeral=True)


@bot.tree.command(name="unmute", description="Retirer le mute (timeout) d'un membre")
@app_commands.describe(membre="Le membre à démuter")
async def unmute(interaction: discord.Interaction, membre: discord.Member):
    if not a_la_permission(interaction):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    try:
        await membre.timeout(None)
        await interaction.response.send_message(f"🔊 {membre.mention} peut de nouveau parler.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de faire ça.", ephemeral=True)


# ============================================================
# LANCEMENT DU BOT
# ============================================================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERREUR : la variable d'environnement DISCORD_TOKEN n'est pas définie.")
        print("   Regarde le fichier GUIDE_HEBERGEMENT.md pour savoir comment la configurer.")
    else:
        bot.run(TOKEN)
