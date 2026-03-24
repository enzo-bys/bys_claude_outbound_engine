"""Agentic copywriting pipeline — 4 specialized agents.

Agent 1 (ANALYST):   Raw enrichment data → LeadBrief (structured understanding)
Agent 2 (STRATEGIST): LeadBrief + CAB-P → Strategy (angle, pain, gap)
Agent 3 (COPYWRITER): LeadBrief + Strategy + company context → Emails
Agent 4 (REVIEWER):   Emails + LeadBrief + Strategy → Score + feedback → rewrite if < 7
"""

from __future__ import annotations
from pathlib import Path

import anthropic

from pipeline.config import CLAUDE_MODEL as DEFAULT_MODEL
from pipeline.models import EnrichedLead, LeadBrief, Strategy, PersonalizedSections, CampaignContext
from pipeline.prompts import build_analyst_prompt, build_strategist_prompt, build_copywriter_prompt, build_reviewer_prompt


# ---------------------------------------------------------------------------
# Tool schemas (structured output via tool_choice)
# ---------------------------------------------------------------------------

BRIEF_TOOL = {
    "name": "lead_brief",
    "description": "Analyse structuree d'un lead.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sector": {
                "type": "string",
                "description": "Le secteur REEL de l'entreprise. Pas 'SaaS B2B' generique mais le metier concret (ex: 'courtage immobilier digital', 'tracabilite RFID dispositifs medicaux', 'agence e-commerce Magento/Shopify').",
            },
            "company_moment": {
                "type": "string",
                "description": "Ce que vit l'entreprise en ce moment (fusion, levee, recrutement, expansion geo, lancement produit...). Basé sur les actualites et signaux.",
            },
            "person_story": {
                "type": "string",
                "description": "L'histoire de cette personne : parcours, transitions, ce qui la rend unique. Ce qu'on comprend de qui elle est.",
            },
            "person_x_moment": {
                "type": "string",
                "description": "L'intersection entre QUI est cette personne et CE QUE VIT sa boite. Le sweet spot. En 1-2 phrases.",
            },
            "daily_reality": {
                "type": "string",
                "description": "Le quotidien concret de cette personne dans son role actuel. Quels sont ses vrais problemes au jour le jour.",
            },
        },
        "required": ["sector", "company_moment", "person_story", "person_x_moment", "daily_reality"],
    },
}

STRATEGY_TOOL = {
    "name": "lead_strategy",
    "description": "Strategie de communication pour un lead.",
    "input_schema": {
        "type": "object",
        "properties": {
            "angle_type": {
                "type": "string",
                "description": "Type d'angle choisi parmi : parcours+momentum, role+news, parcours seul, competences+contexte, news seule.",
            },
            "chosen_pain": {
                "type": "string",
                "description": "Le pain du CAB-P le plus pertinent pour ce lead specifiquement, et pourquoi.",
            },
            "chosen_benefit": {
                "type": "string",
                "description": "Le benefice concret a mettre en avant (pas tous, UN SEUL, le plus percutant pour cette personne).",
            },
            "information_gap": {
                "type": "string",
                "description": "Le gap de curiosite a creer. Quelle info manquante va creer une tension cognitive chez le lecteur ?",
            },
            "key_question": {
                "type": "string",
                "description": "LA question qui va rester dans la tete du lead apres avoir lu l'email. Specifique, ouverte, liee a son quotidien.",
            },
            "why_this_angle": {
                "type": "string",
                "description": "Justification du choix : pourquoi cet angle est le plus fort pour cette personne, dans ce moment.",
            },
        },
        "required": ["angle_type", "chosen_pain", "chosen_benefit", "information_gap", "key_question", "why_this_angle"],
    },
}

EMAILS_TOOL = {
    "name": "write_emails",
    "description": "Emails et messages LinkedIn personnalises.",
    "input_schema": {
        "type": "object",
        "properties": {
            "email1Subject": {"type": "string", "description": "Subject court 2-3 mots lie a LEUR situation"},
            "email1Body": {"type": "string", "description": "Corps complet email 1. Commence par le PRENOM du lead suivi d'une virgule."},
            "email2Subject": {"type": "string", "description": "Subject email 2, format Re: [subject email 1]"},
            "email2Body": {"type": "string", "description": "Corps complet email 2 (relance J+3, angle different)"},
            "email3Subject": {"type": "string", "description": "Subject email 3"},
            "email3Body": {"type": "string", "description": "Corps complet email 3 (dernier message J+17)"},
            "linkedinInvite": {"type": "string", "description": "Invite LinkedIn, max 15 mots"},
            "linkedinDm": {"type": "string", "description": "DM LinkedIn apres connexion, 30-50 mots"},
            "callScript": {"type": "string", "description": "Script d'appel personnalise (5-8 phrases). Accroche, contexte, question ouverte. Ton conversationnel."},
        },
        "required": ["email1Subject", "email1Body", "email2Subject", "email2Body",
                      "email3Subject", "email3Body", "linkedinInvite", "linkedinDm"],
    },
}

REVIEW_TOOL = {
    "name": "review_emails",
    "description": "Evaluation de la qualite des emails.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pertinence_perso": {"type": "integer", "description": "Score 0-3 : est-ce que ca parle de CETTE personne specifiquement ?"},
            "information_gap": {"type": "integer", "description": "Score 0-3 : est-ce que ca cree une question non resolue dans la tete ?"},
            "pattern_break": {"type": "integer", "description": "Score 0-2 : est-ce que ca sort du bruit de la boite mail ?"},
            "naturel": {"type": "integer", "description": "Score 0-2 : est-ce que ca sonne comme un humain sur WhatsApp ?"},
            "total": {"type": "integer", "description": "Score total sur 10"},
            "feedback": {"type": "string", "description": "Si total < 7, feedback precis pour ameliorer. Sinon, vide."},
        },
        "required": ["pertinence_perso", "information_gap", "pattern_break", "naturel", "total", "feedback"],
    },
}


# ---------------------------------------------------------------------------
# Agent functions
# ---------------------------------------------------------------------------

def _build_enrichment_context(lead: EnrichedLead) -> str:
    """Format enrichment data for agent consumption."""
    linkedin = lead.linkedin_profile or {}
    firecrawl = lead.firecrawl_context or {}
    news = firecrawl.get("results", [])

    experience_text = ""
    for i, exp in enumerate(linkedin.get("experience", [])[:3]):
        title = exp.get("title", "")
        company = exp.get("company", "")
        duration = exp.get("duration", "")
        if title or company:
            marker = "Actuel" if i == 0 else f"Avant ({duration})" if duration else "Avant"
            experience_text += f"[{marker}] {title} @ {company}\n"

    skills = linkedin.get("skills", [])
    skills_text = ", ".join(skills[:8]) if skills else "N/A"

    news_text = ""
    for n in news[:3]:
        date = n.get("date", "")
        prefix = f"({date}) " if date else ""
        news_text += f"{prefix}{n.get('title', '')}\n{n.get('snippet', '')[:200]}\n\n"

    li_headline = linkedin.get("headline", "")
    headline = li_headline or lead.headline or "N/A"

    return f"""Prenom : {lead.firstName}
Nom : {lead.lastName}
Entreprise : {lead.companyName}
Titre : {headline}
Intent score : {lead.intent_score}/10

Bio LinkedIn :
{linkedin.get('about', 'N/A')[:400]}

Parcours :
{experience_text or 'Non disponible'}

Competences :
{skills_text}

Actualites entreprise :
{news_text or 'Aucune actualite trouvee.'}"""


async def run_analyst(
    client: anthropic.AsyncAnthropic,
    lead: EnrichedLead,
    ctx: CampaignContext,
) -> LeadBrief:
    """Agent 1: Analyse le lead et produit un brief structure."""
    prompt = f"""Analyse ce lead pour la campagne suivante.

=== CAMPAGNE ===
{ctx.ciblage[:800]}

=== DONNEES LEAD ===
{_build_enrichment_context(lead)}

Produis une analyse structuree avec le tool lead_brief."""

    model = ctx.campaign_config.model if ctx.campaign_config else DEFAULT_MODEL
    response = await client.messages.create(
        model=model,
        max_tokens=600,
        system=build_analyst_prompt(ctx),
        messages=[{"role": "user", "content": prompt}],
        tools=[BRIEF_TOOL],
        tool_choice={"type": "tool", "name": "lead_brief"},
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_block:
        raise ValueError("Analyst: no tool_use block")

    data = tool_block.input
    return LeadBrief(
        firstName=lead.firstName,
        lastName=lead.lastName,
        companyName=lead.companyName,
        sector=data.get("sector", ""),
        company_moment=data.get("company_moment", ""),
        person_story=data.get("person_story", ""),
        person_x_moment=data.get("person_x_moment", ""),
        daily_reality=data.get("daily_reality", ""),
    )


async def run_strategist(
    client: anthropic.AsyncAnthropic,
    brief: LeadBrief,
    ctx: CampaignContext,
) -> Strategy:
    """Agent 2: Choisit l'angle, le pain, et le gap de curiosite."""
    prompt = f"""Voici le brief d'un lead et le contexte business. Choisis la meilleure strategie.

=== BRIEF LEAD ===
Personne : {brief.firstName} {brief.lastName} @ {brief.companyName}
Secteur : {brief.sector}
Moment entreprise : {brief.company_moment}
Histoire personne : {brief.person_story}
Intersection personne x moment : {brief.person_x_moment}
Quotidien : {brief.daily_reality}

=== CAB-P (offre) ===
{ctx.cab_p[:600]}

=== DISCOVERY (qui sommes-nous) ===
{ctx.discovery[:600]}

=== CIBLAGE CAMPAGNE ===
{ctx.ciblage[:400]}

Choisis l'angle, le pain, le gap de curiosite et la question cle. Utilise le tool lead_strategy."""

    model = ctx.campaign_config.model if ctx.campaign_config else DEFAULT_MODEL
    response = await client.messages.create(
        model=model,
        max_tokens=500,
        system=build_strategist_prompt(ctx),
        messages=[{"role": "user", "content": prompt}],
        tools=[STRATEGY_TOOL],
        tool_choice={"type": "tool", "name": "lead_strategy"},
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_block:
        raise ValueError("Strategist: no tool_use block")

    data = tool_block.input
    return Strategy(
        firstName=brief.firstName,
        lastName=brief.lastName,
        angle_type=data.get("angle_type", ""),
        chosen_pain=data.get("chosen_pain", ""),
        chosen_benefit=data.get("chosen_benefit", ""),
        information_gap=data.get("information_gap", ""),
        key_question=data.get("key_question", ""),
        why_this_angle=data.get("why_this_angle", ""),
    )


async def run_copywriter(
    client: anthropic.AsyncAnthropic,
    brief: LeadBrief,
    strategy: Strategy,
    ctx: CampaignContext,
) -> PersonalizedSections:
    """Agent 3: Ecrit les emails a partir du brief et de la strategie."""
    prompt = f"""Ecris les emails et messages LinkedIn pour {brief.firstName}.

=== BRIEF ===
Personne : {brief.firstName} {brief.lastName} @ {brief.companyName}
Secteur : {brief.sector}
Moment : {brief.company_moment}
Son histoire : {brief.person_story}
Intersection personne x moment : {brief.person_x_moment}
Son quotidien : {brief.daily_reality}

=== STRATEGIE ===
Angle : {strategy.angle_type}
Pain a adresser : {strategy.chosen_pain}
Benefice a montrer : {strategy.chosen_benefit}
Gap de curiosite : {strategy.information_gap}
Question cle a poser : {strategy.key_question}
Pourquoi cet angle : {strategy.why_this_angle}

=== QUI SOMMES-NOUS ===
{ctx.discovery[:500]}

=== CE QU'ON PROPOSE ===
{ctx.cab_p[:400]}

Ecris les 3 emails + LinkedIn invite + DM. Liberte totale sur le contenu.
La question cle de la strategie doit apparaitre naturellement dans l'email 1.
Utilise le tool write_emails."""

    model = ctx.campaign_config.model if ctx.campaign_config else DEFAULT_MODEL
    response = await client.messages.create(
        model=model,
        max_tokens=1500,
        system=build_copywriter_prompt(ctx),
        messages=[{"role": "user", "content": prompt}],
        tools=[EMAILS_TOOL],
        tool_choice={"type": "tool", "name": "write_emails"},
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_block:
        raise ValueError("Copywriter: no tool_use block")

    data = tool_block.input
    return PersonalizedSections(
        firstName=brief.firstName,
        lastName=brief.lastName,
        companyName=brief.companyName,
        email1Subject=data.get("email1Subject", ""),
        email1Body=data.get("email1Body", ""),
        email2Subject=data.get("email2Subject", ""),
        email2Body=data.get("email2Body", ""),
        email3Subject=data.get("email3Subject", ""),
        email3Body=data.get("email3Body", ""),
        linkedinInvite=data.get("linkedinInvite", ""),
        linkedinDm=data.get("linkedinDm", ""),
        callScript=data.get("callScript", ""),
    )


async def run_reviewer(
    client: anthropic.AsyncAnthropic,
    sections: PersonalizedSections,
    brief: LeadBrief,
    strategy: Strategy,
    ctx: CampaignContext | None = None,
) -> tuple[int, str]:
    """Agent 4: Review les emails et retourne (score, feedback)."""
    prompt = f"""Evalue ces emails pour {brief.firstName} {brief.lastName} @ {brief.companyName}.

=== CONTEXTE LEAD ===
Secteur : {brief.sector}
Intersection personne x moment : {brief.person_x_moment}
Quotidien : {brief.daily_reality}

=== STRATEGIE PREVUE ===
Angle : {strategy.angle_type}
Gap de curiosite voulu : {strategy.information_gap}
Question cle prevue : {strategy.key_question}

=== EMAILS A EVALUER ===
Email 1 [{sections.email1Subject}] :
{sections.email1Body}

Email 2 [{sections.email2Subject}] :
{sections.email2Body}

Email 3 [{sections.email3Subject}] :
{sections.email3Body}

LinkedIn invite : {sections.linkedinInvite}
LinkedIn DM : {sections.linkedinDm}

Evalue selon les 4 criteres (pertinence_perso, information_gap, pattern_break, naturel).
Utilise le tool review_emails."""

    model = (ctx.campaign_config.model if ctx and ctx.campaign_config else DEFAULT_MODEL)
    reviewer_prompt = build_reviewer_prompt(ctx) if ctx else build_reviewer_prompt(CampaignContext(campaign_dir=Path("."), client_dir=Path("."), campaign_name=""))
    response = await client.messages.create(
        model=model,
        max_tokens=400,
        system=reviewer_prompt,
        messages=[{"role": "user", "content": prompt}],
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "review_emails"},
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_block:
        raise ValueError("Reviewer: no tool_use block")

    data = tool_block.input
    score = data.get("total", 0)
    feedback = data.get("feedback", "")
    return score, feedback


async def run_rewrite(
    client: anthropic.AsyncAnthropic,
    sections: PersonalizedSections,
    brief: LeadBrief,
    strategy: Strategy,
    feedback: str,
    ctx: CampaignContext | None = None,
) -> PersonalizedSections:
    """Rewrite emails based on reviewer feedback."""
    prompt = f"""Reecris les emails pour {brief.firstName}. Le reviewer a trouve des problemes.

=== FEEDBACK DU REVIEWER ===
{feedback}

=== BRIEF ===
Secteur : {brief.sector}
Intersection personne x moment : {brief.person_x_moment}
Son quotidien : {brief.daily_reality}

=== STRATEGIE ===
Angle : {strategy.angle_type}
Gap de curiosite : {strategy.information_gap}
Question cle : {strategy.key_question}

=== EMAILS ACTUELS (a ameliorer) ===
Email 1 [{sections.email1Subject}] :
{sections.email1Body}

Email 2 [{sections.email2Subject}] :
{sections.email2Body}

Email 3 [{sections.email3Subject}] :
{sections.email3Body}

LinkedIn invite : {sections.linkedinInvite}
LinkedIn DM : {sections.linkedinDm}

Corrige les problemes signales par le reviewer. Garde ce qui fonctionne.
Utilise le tool write_emails."""

    model = (ctx.campaign_config.model if ctx and ctx.campaign_config else DEFAULT_MODEL)
    rewrite_prompt = build_copywriter_prompt(ctx) if ctx else build_copywriter_prompt(CampaignContext(campaign_dir=Path("."), client_dir=Path("."), campaign_name=""))
    response = await client.messages.create(
        model=model,
        max_tokens=1500,
        system=rewrite_prompt,
        messages=[{"role": "user", "content": prompt}],
        tools=[EMAILS_TOOL],
        tool_choice={"type": "tool", "name": "write_emails"},
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_block:
        raise ValueError("Rewrite: no tool_use block")

    data = tool_block.input
    return PersonalizedSections(
        firstName=brief.firstName,
        lastName=brief.lastName,
        companyName=brief.companyName,
        email1Subject=data.get("email1Subject", ""),
        email1Body=data.get("email1Body", ""),
        email2Subject=data.get("email2Subject", ""),
        email2Body=data.get("email2Body", ""),
        email3Subject=data.get("email3Subject", ""),
        email3Body=data.get("email3Body", ""),
        linkedinInvite=data.get("linkedinInvite", ""),
        linkedinDm=data.get("linkedinDm", ""),
        callScript=data.get("callScript", ""),
    )
