import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import anthropic

logging.basicConfig(level=logging.INFO)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Memoria de conversación por usuario
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente personal con IA. ¿En qué te puedo ayudar hoy? 🤖"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_text = update.message.text

    # Inicializar historial si es nuevo usuario
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Agregar mensaje del usuario al historial
    conversation_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Mantener solo los últimos 10 mensajes para no gastar tokens
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Eres un asistente personal inteligente, amigable y útil. Respondes en el mismo idioma que el usuario. Eres conciso pero completo en tus respuestas.",
            messages=conversation_history[user_id]
        )

        assistant_reply = response.content[0].text

        # Guardar respuesta en el historial
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        await update.message.reply_text(assistant_reply)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Hubo un error, intenta de nuevo en un momento.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    conversation_history[user_id] = []
    await update.message.reply_text("✅ Conversación reiniciada. ¡Empecemos de nuevo!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot corriendo...")
    app.run_polling()
