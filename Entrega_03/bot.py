"""Bot de Telegram: Cifrado César + Modelos de Markov.
Uso:  export TELEGRAM_TOKEN="tu_token"   (Windows: set TELEGRAM_TOKEN=...)
      python bot.py
"""
import asyncio
import io
import logging
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import cesar
import markov
import scraper

logging.basicConfig(level=logging.INFO)
DATOS = Path("datos")
DATOS.mkdir(exist_ok=True)
K_MAX, N_MAX = 10, 4000          # N_MAX < 4096 (límite de Telegram)
MIN_TEXTO = 50

AYUDA = (
    "🤖 *Bot de Criptografía y Markov*\n\n"
    "*Cifrado César*\n"
    "/cifrar `<desplazamiento> <mensaje>`\n"
    "   Ej: `/cifrar 15 Este es UN mensaje c1fr4d0`\n"
    "/descifrar `<mensaje>` — descubre el desplazamiento solo\n"
    "   Ej: `/descifrar THIt tH 92 BtCHpyt`\n\n"
    "*Cadenas de Markov*\n"
    "/scrapear `<url>` — descarga el texto de un sitio estático\n"
    "   Ej: `/scrapear https://es.wikipedia.org/wiki/Python`\n"
    "/markov `<K> <N>` — genera N caracteres con un modelo de orden K\n"
    "   Ej: `/markov 3 500`  (K: 0-10, N: 1-4000)\n"
    "/histograma `<K>` — histograma de frecuencias de las K-tuplas\n"
    "   Ej: `/histograma 2`  (K: 0-10)\n\n"
    "/ayuda — muestra este mensaje\n\n"
    f"Alfabeto del César: `{cesar.ALFABETO}`\n"
    "Los caracteres fuera del alfabeto (espacios, comas, etc.) no se modifican."
)


def _archivo(update: Update) -> Path:
    return DATOS / f"{update.effective_user.id}.txt"


def _entero(s: str):
    try:
        return int(s)
    except ValueError:
        return None


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(AYUDA, parse_mode="Markdown")


# ---------------- César ----------------
async def cmd_cifrar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    partes = (update.message.text or "").split(maxsplit=2)
    if len(partes) < 3 or _entero(partes[1]) is None:
        await update.message.reply_text(
            "⚠️ Formato: /cifrar <desplazamiento> <mensaje>\n"
            "El desplazamiento debe ser un número entero.\n"
            "Ejemplo: /cifrar 15 Hola mundo 123")
        return
    k = _entero(partes[1])
    resultado = cesar.cifrar(partes[2], k)
    await update.message.reply_text(
        f"🔒 Desplazamiento efectivo: {k % cesar.N}\n{resultado}")


async def cmd_descifrar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    partes = (update.message.text or "").split(maxsplit=1)
    if len(partes) < 2 or not partes[1].strip():
        await update.message.reply_text(
            "⚠️ Formato: /descifrar <mensaje cifrado>\n"
            "No necesitas indicar el desplazamiento.\n"
            "Ejemplo: /descifrar THIt tH 92 BtCHpyt")
        return
    cands = cesar.descifrar(partes[1].strip(), top=3)
    lineas = ["🔓 Candidatos (el primero es el más probable):"]
    for i, (k, texto, _) in enumerate(cands, 1):
        lineas.append(f"\n{i}) desplazamiento {k}:\n{texto}")
    await update.message.reply_text("\n".join(lineas))


# ---------------- Markov ----------------
async def cmd_scrapear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if len(args) != 1 or not scraper.url_valida(args[0]):
        await update.message.reply_text(
            "⚠️ Formato: /scrapear <url>\n"
            "La URL debe empezar por http:// o https://\n"
            "Ejemplo: /scrapear https://es.wikipedia.org/wiki/Python")
        return
    await update.message.reply_text("⏳ Descargando…")
    try:
        texto = await asyncio.to_thread(scraper.obtener_texto, args[0])
    except Exception as e:
        await update.message.reply_text(f"❌ No se pudo obtener el texto: {e}")
        return
    if len(texto) < MIN_TEXTO:
        await update.message.reply_text(
            "❌ La página tiene muy poco texto (¿se carga con JavaScript?). "
            "Prueba con un sitio estático.")
        return
    _archivo(update).write_text(texto, encoding="utf-8")
    await update.message.reply_text(
        f"✅ Texto guardado ({len(texto)} caracteres).\n"
        f"Vista previa: {texto[:150]}…\n\n"
        "Ahora usa /markov <K> <N> o /histograma <K>.")


def _cargar(update: Update):
    f = _archivo(update)
    return markov.limpiar(f.read_text(encoding="utf-8")) if f.exists() else None


async def cmd_markov(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    k = _entero(args[0]) if len(args) == 2 else None
    n = _entero(args[1]) if len(args) == 2 else None
    if k is None or n is None or not (0 <= k <= K_MAX) or not (1 <= n <= N_MAX):
        await update.message.reply_text(
            f"⚠️ Formato: /markov <K> <N>\nK entero entre 0 y {K_MAX}, "
            f"N entero entre 1 y {N_MAX}.\nEjemplo: /markov 3 500")
        return
    texto = _cargar(update)
    if texto is None:
        await update.message.reply_text("⚠️ Primero usa /scrapear <url>.")
        return
    if k >= len(texto):
        await update.message.reply_text("⚠️ K es mayor que el texto disponible.")
        return
    generado = await asyncio.to_thread(markov.generar, texto, k, n)
    await update.message.reply_text(generado)


async def cmd_histograma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    k = _entero(ctx.args[0]) if len(ctx.args) == 1 else None
    if k is None or not (0 <= k <= K_MAX):
        await update.message.reply_text(
            f"⚠️ Formato: /histograma <K>\nK entero entre 0 y {K_MAX}.\n"
            "Ejemplo: /histograma 2")
        return
    texto = _cargar(update)
    if texto is None:
        await update.message.reply_text("⚠️ Primero usa /scrapear <url>.")
        return
    if k >= len(texto):
        await update.message.reply_text("⚠️ K es mayor que el texto disponible.")
        return
    frec = markov.frecuencias_ktuplas(texto, k)
    top = frec.most_common(20)
    etiquetas = [t.replace(" ", "␣") for t, _ in top]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(top)), [v for _, v in top], color="#4c72b0")
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(etiquetas, rotation=60, ha="right")
    ax.set_title(f"Top {len(top)} de {len(frec)} {k}-tuplas distintas "
                 "(␣ = espacio)" if k else
                 f"Top {len(top)} caracteres (K=0, ␣ = espacio)")
    ax.set_ylabel("Frecuencia")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    await update.message.reply_photo(buf)


async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("ayuda", "Qué hace el bot y sus comandos"),
        BotCommand("cifrar", "Cifrar: <desplazamiento> <mensaje>"),
        BotCommand("descifrar", "Descifrar: <mensaje>"),
        BotCommand("scrapear", "Descargar texto de una URL"),
        BotCommand("markov", "Generar texto: <K> <N>"),
        BotCommand("histograma", "Histograma de K-tuplas: <K>"),
    ])


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("Define la variable de entorno TELEGRAM_TOKEN.")
    app = Application.builder().token(token).post_init(post_init).build()
    for nombre, fn in [("start", start), ("ayuda", start),
                       ("cifrar", cmd_cifrar), ("descifrar", cmd_descifrar),
                       ("scrapear", cmd_scrapear), ("markov", cmd_markov),
                       ("histograma", cmd_histograma)]:
        app.add_handler(CommandHandler(nombre, fn))
    app.run_polling()


if __name__ == "__main__":
    main()