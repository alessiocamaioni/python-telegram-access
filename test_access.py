#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Prova d'uso del modulo _accesstelegram.py

import logging
import telegram
from telegram import Emoji, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from configobj import ConfigObj

from _accesstelegram import Check

# Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG) #livello DEBUG
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO) #livello INFO
logger = logging.getLogger(__name__)

##########################################################

# Config file inserire token nel file .ini
config_ini = ConfigObj('test_access_config.ini')
log = config_ini['GestioneLog']['log']
telegram_token = config_ini['TokenBotTelegram']['telegram_token']

try:
	YES_UP, NO_DOWN, NO_ENTRY, WRENCH, PAGE_FACING_UP, USERS, BACK = (Emoji.THUMBS_UP_SIGN.decode('utf-8'), Emoji.THUMBS_DOWN_SIGN.decode('utf-8'), Emoji.NO_ENTRY.decode('utf-8'), Emoji.WRENCH.decode('utf-8'), Emoji.PAGE_FACING_UP.decode('utf-8'), Emoji.RESTROOM.decode('utf-8'), Emoji.BACK_WITH_LEFTWARDS_ARROW_ABOVE.decode('utf-8'))
except AttributeError:
	YES_UP, NO_DOWN, NO_ENTRY, WRENCH, PAGE_FACING_UP, USERS, BACK = (Emoji.THUMBS_UP_SIGN, Emoji.THUMBS_DOWN_SIGN, Emoji.NO_ENTRY, Emoji.WRENCH, Emoji.PAGE_FACING_UP, Emoji.RESTROOM, Emoji.BACK_WITH_LEFTWARDS_ARROW_ABOVE)

help_text = (
	"<b>Comandi per la gestione degli utenti:</b>\n"
	"/userslist Visualizza lista di tutti gli utenti\n"
	"/users Visualizza lista utenti\n"
	"/bans Visualizza lista bannati\n"
	"/deluser Visualizza lista utenti per la cancellazione\n"
	"/delban Visualizza lista bannati per la cancellazione\n"
	"/delallusers Cancella tutti gli utenti\n"
	"/delallbans Cancella tutti gli utenti bannati\n"
)
welcome_text = USERS+" TestBot per la gestione degli accessi ..."

button_command=[WRENCH+' GESTIONE UTENTI',PAGE_FACING_UP+' LISTA UTENTI COMPLETA',YES_UP+' LISTA UTENTI',NO_DOWN+' LISTA BANNATI','CANCELLAZIONE UTENTE','CANCELLAZIONE BANNATO','CANCELLA TUTTI GLI UTENTI','CANCELLA TUTTI I BANNATI',BACK]

clear_keyboard = telegram.ReplyKeyboardHide()

menu_keyboard = telegram.ReplyKeyboardMarkup([[WRENCH+' GESTIONE UTENTI']])
menu_keyboard.one_time_keyboard=False
menu_keyboard.resize_keyboard=True 

menu_gestione_utenti_keyboard = telegram.ReplyKeyboardMarkup([[PAGE_FACING_UP+' LISTA UTENTI COMPLETA'],[YES_UP+' LISTA UTENTI',NO_DOWN+' LISTA BANNATI'],['CANCELLAZIONE UTENTE','CANCELLAZIONE BANNATO'],['CANCELLA TUTTI GLI UTENTI','CANCELLA TUTTI I BANNATI'], [BACK]])
menu_gestione_utenti_keyboard.one_time_keyboard=False
menu_gestione_utenti_keyboard.resize_keyboard=True 	

check=Check()

def messaggi_in_arrivo(bot, update):
	#Prima di elaborare un messaggio controlla che tipo di utente e':
	user_type = check.user(bot,update)
	
	if user_type[0]=="none":
		contact_admin = ['',"@{0}".format(user_type[1])][user_type[1] != '']
		bot.sendMessage(update.message.chat_id, "%s <b>Accesso negato!</b>\n Contattare l'amministratore! %s" % (NO_ENTRY, contact_admin), parse_mode=telegram.ParseMode.HTML)
		return

	if user_type[0]=="user":
		bot.sendMessage(update.message.chat_id, "User\n UserID: %s" % update.message.from_user.id)
		return
	
	if user_type[0]=="admin":
		if update.message.text in button_command :
			if update.message.text==button_command[0] : # or WRENCH+' GESTIONE UTENTI'
				print "- click tasto gestione utenti"
				bot.sendMessage(update.message.chat_id, "Seleziona il comando desiderato:", reply_markup=menu_gestione_utenti_keyboard)
			if update.message.text==button_command[1] : # PAGE_FACING_UP+' LISTA UTENTI COMPLETA' 
				print "- click LISTA UTENTI COMPLETA"
				check.cmd_userslist(bot,update)
			if update.message.text==button_command[2] : # YES_UP+'LISTA UTENTI' 
				print "- click LISTA UTENTI"
				check.cmd_users(bot,update)
			if update.message.text==button_command[3] : # NO_DOWN+'LISTA BANNATI'  
				print "- click LISTA BANNATI"
				check.cmd_bans(bot,update)
			if update.message.text==button_command[4] : # 'CANCELLAZIONE UTENTE' 
				print "- click CANCELLAZIONE UTENTE"
				check.cmd_deluser(bot,update)
			if update.message.text==button_command[5] : # 'CANCELLAZIONE BANNATO' 
				print "- click CANCELLAZIONE BANNATO"
				check.cmd_delban(bot,update)
			if update.message.text==button_command[6] : # 'CANCELLA TUTTI GLI UTENTI' 
				print "- click CANCELLA TUTTI GLI UTENTI"
				check.cmd_delallusers(bot,update)
			if update.message.text==button_command[7] : # 'CANCELLA TUTTI I BANNATI' 
				print "- click CANCELLA TUTTI I BANNATI"
				check.cmd_delallbans(bot,update)
			if update.message.text==button_command[8] : # BACK 
				print "- click BACK"
				menu(bot,update)
		else:
			bot.sendMessage(update.message.chat_id, "Admin\n UserID: %s" % update.message.from_user.id)
		return
	
def comando_start(bot, update):	
	#Prima di elaborare un comando controlla che tipo di utente e':
	user_type = check.user(bot,update)
	
	if user_type[0]=="none":
		bot.sendMessage(update.message.chat_id, welcome_text)
		contact_admin = ['',"@{0}".format(user_type[1])][user_type[1] != '']
		bot.sendMessage(update.message.chat_id, "Accesso negato!\n Contattare l'amministratore! {0}".format(contact_admin))
		return
	
	if user_type[0]=="user_auth":
		bot.sendMessage(update.message.chat_id, welcome_text)
		bot.sendMessage(update.message.chat_id, "Accesso in attesa di approvazione!")
		return

	if user_type[0]=="user":
		bot.sendMessage(update.message.chat_id, welcome_text)
		bot.sendMessage(update.message.chat_id, text="Salve User!")
		return

	if user_type[0]=="admin":
		bot.sendMessage(update.message.chat_id, welcome_text)
		bot.sendMessage(update.message.chat_id, "Salve Admin!")
		menu(bot,update)
		return

def menu(bot, update):
	#Prima di elaborare un comando controlla che tipo di utente e':
	user_type = check.user(bot,update)
	
	if user_type[0]=="admin":
		bot.sendMessage(update.message.chat_id, help_text, parse_mode=telegram.ParseMode.HTML, reply_markup=menu_keyboard)
		return
	else :
		bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
	
	
# updater = Updater(token='154208494:AAEL7oNAP8shSshQIRIYTOfGBeaIkfpxsow')
updater = Updater(telegram_token)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler([Filters.text], messaggi_in_arrivo))
dispatcher.add_handler(CommandHandler("start",comando_start))
dispatcher.add_handler(CommandHandler("menu", menu))
dispatcher.add_handler(CommandHandler("help", menu))
check.addAccessCheckCommandHandler(dispatcher)
updater.start_polling()
updater.idle()