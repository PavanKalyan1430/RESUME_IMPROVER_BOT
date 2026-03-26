from __future__ import annotations

import io
import logging
import os
import tempfile
from dataclasses import dataclass, field

import discord
from dotenv import load_dotenv

from resume_parser import ResumeParseError, extract_text_from_file, normalize_resume_text
from resume_pdf import THEMES, build_resume_pdf
from resume_workflow import (
    call_analyze_api,
    call_rewrite_api,
    format_final_response,
    format_initial_analysis,
    format_template_options,
)


load_dotenv()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
COMMAND_PREFIX = "!"
MAX_MESSAGE_LENGTH = 1900


@dataclass
class DiscordSession:
    jd: str | None = None
    resume_text: str | None = None
    analysis: dict | None = None
    improved_resume: str | None = None
    rescored_analysis: dict | None = None
    selected_template: str | None = None
    resume_filename: str = "resume.pdf"
    missing_keywords: list[str] = field(default_factory=list)
    state: str = "idle"


sessions: dict[int, DiscordSession] = {}


def get_session(user_id: int) -> DiscordSession:
    if user_id not in sessions:
        sessions[user_id] = DiscordSession()
    return sessions[user_id]


def reset_session(user_id: int) -> DiscordSession:
    session = DiscordSession()
    sessions[user_id] = session
    return session


def build_client() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    return discord.Client(intents=intents)


class TemplateSelectView(discord.ui.View):
    def __init__(self, user_id: int) -> None:
        super().__init__(timeout=300)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This style picker belongs to another user. Run `!start` to begin your own session.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="ATS Style", style=discord.ButtonStyle.secondary)
    async def ats_style(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle_template(interaction, "ATS Resume")

    @discord.ui.button(label="Modern Style", style=discord.ButtonStyle.primary)
    async def modern_style(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle_template(interaction, "Modern Resume")

    @discord.ui.button(label="Creative Style", style=discord.ButtonStyle.success)
    async def creative_style(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle_template(interaction, "Creative Resume")

    async def _handle_template(self, interaction: discord.Interaction, template: str) -> None:
        session = get_session(self.user_id)
        if not session.jd or not session.resume_text or not session.analysis:
            await interaction.response.send_message(
                "Your session expired. Run `!start` and send the job description again.",
                ephemeral=True,
            )
            return

        session.selected_template = template
        await interaction.response.edit_message(
            content=f"Selected style: {template}\n\nRewriting and formatting your resume as a PDF...",
            view=None,
        )

        try:
            rewrite_response = await call_rewrite_api(
                jd=session.jd,
                resume_text=session.resume_text,
                template=template,
            )
        except Exception as exc:
            logger.exception("Resume rewrite failed")
            await interaction.followup.send(f"Rewrite failed: {exc}")
            return

        session.improved_resume = rewrite_response["improved_resume"]
        session.rescored_analysis = rewrite_response["analysis"]
        old_score = float(session.analysis["score"])
        new_score = float(session.rescored_analysis["score"])
        improvement = round(new_score - old_score, 1)

        await send_long_message(interaction.channel, format_final_response(old_score, new_score, improvement))
        await send_long_message(interaction.channel, "Improved Resume:\n\n" + session.improved_resume)

        pdf_content, pdf_filename = build_resume_pdf(
            resume_text=session.improved_resume,
            template=template,
            source_filename=session.resume_filename,
        )
        file = discord.File(io.BytesIO(pdf_content), filename=pdf_filename)
        await interaction.followup.send(
            content=f"Download your rewritten resume as a styled PDF ({template}).",
            file=file,
        )
        session.state = "done"
        await interaction.followup.send("Use `!start` or `!analyze` to start another review.")


async def send_long_message(channel: discord.abc.Messageable, text: str) -> None:
    for start in range(0, len(text), MAX_MESSAGE_LENGTH):
        await channel.send(text[start : start + MAX_MESSAGE_LENGTH])


async def extract_text_from_discord_message(message: discord.Message, file_type_name: str = "resume") -> tuple[str, str]:
    if message.attachments:
        attachment = message.attachments[0]
        suffix = os.path.splitext(attachment.filename or "")[1].lower()
        if suffix not in {".pdf", ".txt", ".md"}:
            raise ResumeParseError(f"Unsupported file type. Please upload a PDF or text file for the {file_type_name}.")

        file_bytes = await attachment.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            return extract_text_from_file(temp_path), attachment.filename or f"{file_type_name}.txt"
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning("Failed to remove temp file %s", temp_path)

    if message.content:
        return normalize_resume_text(message.content), f"{file_type_name}.txt"

    raise ResumeParseError(f"Please upload a PDF/TXT or paste the {file_type_name} text.")


client = build_client()


@client.event
async def on_ready() -> None:
    logger.info("Discord bot logged in as %s", client.user)


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    content = message.content.strip()
    user_id = message.author.id
    session = get_session(user_id)

    if content.lower() in {f"{COMMAND_PREFIX}start", f"{COMMAND_PREFIX}analyze"}:
        session = reset_session(user_id)
        session.state = "waiting_jd"
        await message.channel.send(
            "Welcome to AI Resume Analyzer Bot for Discord.\n\n"
            "Send the job description first, and then I will ask for the resume."
        )
        return

    if content.lower() == f"{COMMAND_PREFIX}cancel":
        reset_session(user_id)
        await message.channel.send("Cancelled the current session. Use `!start` to begin again.")
        return

    if session.state == "idle":
        return

    if session.state == "waiting_jd":
        try:
            jd_text, _ = await extract_text_from_discord_message(message, "job description")
        except ResumeParseError as exc:
            await message.channel.send(str(exc))
            return

        if len(jd_text) < 20:
            await message.channel.send("The job description is too short. Please send a fuller JD.")
            return

        session.jd = jd_text
        session.state = "waiting_resume"
        await message.channel.send("Job description saved.\n\nNow send the resume as a PDF, TXT file, or plain text.")
        return

    if session.state == "waiting_resume":
        if not session.jd:
            session.state = "waiting_jd"
            await message.channel.send("Please send the job description first with `!start`.")
            return

        try:
            resume_text, filename = await extract_text_from_discord_message(message, "resume")
        except ResumeParseError as exc:
            await message.channel.send(str(exc))
            return

        session.resume_text = resume_text
        session.resume_filename = filename

        async with message.channel.typing():
            try:
                analysis = await call_analyze_api(session.jd, session.resume_text)
            except Exception as exc:
                logger.exception("Resume analysis failed")
                await message.channel.send(f"Analysis failed: {exc}")
                return

        session.analysis = analysis
        session.missing_keywords = analysis.get("missing_keywords", [])
        session.state = "waiting_template"

        await send_long_message(message.channel, format_initial_analysis(analysis))
        if session.missing_keywords:
            await send_long_message(
                message.channel,
                "Missing Keywords:\n" + "\n".join(f"- {keyword}" for keyword in session.missing_keywords),
            )

        await message.channel.send(format_template_options(), view=TemplateSelectView(user_id=user_id))
        return


def main() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured.")
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
