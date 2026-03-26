from __future__ import annotations

import io
import logging
import os
import tempfile
from dataclasses import dataclass, field

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from resume_parser import ResumeParseError, extract_text_from_file, normalize_resume_text
from resume_pdf import build_resume_pdf
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

WAITING_JD, WAITING_RESUME = range(2)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


@dataclass
class UserSession:
    jd: str | None = None
    resume_text: str | None = None
    analysis: dict | None = None
    improved_resume: str | None = None
    rescored_analysis: dict | None = None
    selected_template: str | None = None
    resume_filename: str = "resume.pdf"
    missing_keywords: list[str] = field(default_factory=list)


def get_session(context: ContextTypes.DEFAULT_TYPE) -> UserSession:
    session = context.user_data.get("session")
    if session is None:
        session = UserSession()
        context.user_data["session"] = session
    return session


def reset_session(context: ContextTypes.DEFAULT_TYPE) -> UserSession:
    session = UserSession()
    context.user_data["session"] = session
    return session


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reset_session(context)
    await update.message.reply_text(
        "Welcome to AI Resume Analyzer Bot.\n\n"
        "Send the job description first, and then I will ask for the resume."
    )
    return WAITING_JD


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reset_session(context)
    await update.message.reply_text("Send the job description you want to target.")
    return WAITING_JD


async def _extract_jd_from_message(update: Update) -> str:
    """Extracts Job Description text from a message, which can be text or a document."""
    message = update.message
    if message.document:
        document = message.document
        suffix = os.path.splitext(document.file_name or "")[1].lower()
        if suffix not in {".pdf", ".txt", ".md"}:
            raise ResumeParseError(
                "Unsupported file type. Please upload a PDF, TXT, or MD file for the Job Description."
            )

        telegram_file = await document.get_file()
        file_bytes = await telegram_file.download_as_bytearray()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            return extract_text_from_file(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning("Failed to remove temp file %s", temp_path)

    if message.text:
        return message.text.strip()

    raise ResumeParseError("Please upload a PDF/TXT/MD file or paste the job description text.")


async def receive_jd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return WAITING_JD

    try:
        jd_text = await _extract_jd_from_message(update)
    except ResumeParseError as exc:
        await update.message.reply_text(str(exc))
        return WAITING_JD
    except Exception as exc:
        logger.exception("Error extracting JD")
        await update.message.reply_text(f"An error occurred: {exc}")
        return WAITING_JD

    if len(jd_text) < 20:
        await update.message.reply_text("The job description is too short. Please send a fuller JD.")
        return WAITING_JD

    session = get_session(context)
    session.jd = jd_text
    await update.message.reply_text(
        "Job description saved.\n\n"
        "Now send the resume as a PDF, TXT file, or plain text."
    )
    return WAITING_RESUME


async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return WAITING_RESUME

    session = get_session(context)
    if not session.jd:
        await update.message.reply_text("Please send the job description first with /start.")
        return WAITING_JD

    try:
        resume_text, filename = await _extract_resume_from_message(update)
    except ResumeParseError as exc:
        await update.message.reply_text(str(exc))
        return WAITING_RESUME

    session.resume_text = resume_text
    session.resume_filename = filename

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        analysis = await call_analyze_api(session.jd, session.resume_text)
    except Exception as exc:
        logger.exception("Resume analysis failed")
        await update.message.reply_text(f"Analysis failed: {exc}")
        return WAITING_RESUME

    session.analysis = analysis
    session.missing_keywords = analysis.get("missing_keywords", [])

    await update.message.reply_text(format_initial_analysis(analysis))
    if session.missing_keywords:
        await update.message.reply_text(
            "Missing Keywords:\n" + "\n".join(f"- {keyword}" for keyword in session.missing_keywords)
        )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ATS Style", callback_data="template:ATS Resume"),
                InlineKeyboardButton("Modern Style", callback_data="template:Modern Resume"),
            ],
            [InlineKeyboardButton("Creative Style", callback_data="template:Creative Resume")],
        ]
    )
    await update.message.reply_text(
        format_template_options(),
        reply_markup=keyboard,
    )
    return ConversationHandler.END


async def template_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    session = get_session(context)
    if not session.jd or not session.resume_text or not session.analysis:
        await query.edit_message_text("Session expired. Please restart with /start.")
        return

    template = query.data.split("template:", 1)[1]
    session.selected_template = template
    await query.edit_message_text(f"Selected style: {template}\n\nRewriting and formatting your resume as a PDF...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        rewrite_response = await call_rewrite_api(
            jd=session.jd,
            resume_text=session.resume_text,
            template=template,
        )
    except Exception as exc:
        logger.exception("Resume rewrite failed")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Rewrite failed: {exc}")
        return

    session.improved_resume = rewrite_response["improved_resume"]
    session.rescored_analysis = rewrite_response["analysis"]

    old_score = float(session.analysis["score"])
    new_score = float(session.rescored_analysis["score"])
    improvement = round(new_score - old_score, 1)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=format_final_response(old_score, new_score, improvement),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Improved Resume:\n\n" + session.improved_resume,
    )

    pdf_content, pdf_filename = build_resume_pdf(
        resume_text=session.improved_resume,
        template=template,
        source_filename=session.resume_filename,
    )
    resume_bytes = io.BytesIO(pdf_content)
    resume_bytes.name = pdf_filename
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=resume_bytes,
        filename=pdf_filename,
        caption=f"Download your rewritten resume as a styled PDF ({template}).",
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Use /analyze to start another review.",
    )
    return


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reset_session(context)
    await update.message.reply_text("Cancelled the current session. Use /start to begin again.")
    return ConversationHandler.END


async def unsupported_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("Please type /start to begin, or send a job description as text or PDF.")
    return ConversationHandler.END


async def _extract_resume_from_message(update: Update) -> tuple[str, str]:
    message = update.message
    if message.document:
        document = message.document
        suffix = os.path.splitext(document.file_name or "")[1].lower()
        if suffix not in {".pdf", ".txt", ".md"}:
            raise ResumeParseError("Unsupported file type. Please upload a PDF or text file.")

        telegram_file = await document.get_file()
        file_bytes = await telegram_file.download_as_bytearray()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            return extract_text_from_file(temp_path), document.file_name or "resume.txt"
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning("Failed to remove temp file %s", temp_path)

    if message.text:
        return normalize_resume_text(message.text), "resume.txt"

    raise ResumeParseError("Please upload a PDF/TXT resume or paste the resume text.")

def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("analyze", analyze_command),
            MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.Document.ALL, receive_jd),
        ],
        states={
            WAITING_JD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_jd),
                MessageHandler(filters.Document.ALL, receive_jd),
            ],
            WAITING_RESUME: [
                MessageHandler(filters.Document.ALL, receive_resume),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_resume),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("analyze", analyze_command),
            CommandHandler("cancel", cancel),
        ],
    )
    application.add_handler(conversation_handler)
    application.add_handler(CallbackQueryHandler(template_selected, pattern=r"^template:"))
    application.add_handler(MessageHandler(filters.ALL, unsupported_message))
    return application


def main() -> None:
    application = build_application()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
