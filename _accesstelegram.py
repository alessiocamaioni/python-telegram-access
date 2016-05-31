#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Classe per il controllo degli accessi verso un Bot Telegram
#
# V 0.8
#
# richiede: sudo pip install configobj

import random
import json
import os.path
import telegram
from telegram import Emoji, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from configobj import ConfigObj

class Check():
	global log
	global clear_keyboard
	global state
	global index_self_ban_id
	global MENU, AWAIT_CONFIRMATION, AWAIT_INPUT
	global YES_USER_AUTH, NO__USER_AUTH, NO_ENTRY, PAGE_FACING_UP
	global tmp_first_name, tmp_last_name, tmp_username, admin_commands

	# Lettura Config file
	config_ini = ConfigObj('_accesstelegram_config.ini')
	log = config_ini['GestioneLog']['log']
	user_file = config_ini['ConfigFiles']['user_file']
	ban_user_file = config_ini['ConfigFiles']['ban_user_file']
	
	user_ids=[]
	user_first_names=[]
	user_last_names=[]
	user_nicks=[]
	ban_user_ids=[]
	ban_user_first_names=[]
	ban_user_last_names=[]
	ban_user_nicks=[]
	index_self_ban_id=''
	clear_keyboard = telegram.ReplyKeyboardHide()
	
	# Define the different states a chat can be in
	MENU, AWAIT_CONFIRMATION, AWAIT_INPUT = range(3)

	# Python 2 and 3 unicode differences
	try:
		YES_USER_AUTH, NO__USER_AUTH, NO_ENTRY, PAGE_FACING_UP = (Emoji.THUMBS_UP_SIGN.decode('utf-8'), Emoji.THUMBS_DOWN_SIGN.decode('utf-8'), Emoji.NO_ENTRY.decode('utf-8'), Emoji.PAGE_FACING_UP.decode('utf-8'))
	except AttributeError:
		YES_USER_AUTH, NO__USER_AUTH, NO_ENTRY, PAGE_FACING_UP = (Emoji.THUMBS_UP_SIGN, Emoji.THUMBS_DOWN_SIGN, Emoji.NO_ENTRY, Emoji.PAGE_FACING_UP)

	# States are saved in a dict that maps chat_id -> state
	state = dict()
	
	# Dict for temp archive userinfo 
	tmp_first_name = dict()
	tmp_last_name = dict()
	tmp_username = dict()
	
	admin_commands = [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
	admin_commands[0] = '/userslist'
	admin_commands[1] = '/users'
	admin_commands[2] = '/bans'
	admin_commands[3] = '/deluser'
	admin_commands[4] = '/delban'
	admin_commands[5] = '/delallusers'
	admin_commands[6] = '/delallbans'
	admin_commands[7] = PAGE_FACING_UP+' LISTA UTENTI COMPLETA'
	admin_commands[8] = YES_USER_AUTH+' LISTA UTENTI'
	admin_commands[9] = NO__USER_AUTH+' LISTA BANNATI'
	admin_commands[10] = 'CANCELLAZIONE UTENTE'
	admin_commands[11] = 'CANCELLAZIONE BANNATO'
	admin_commands[12] = 'CANCELLA TUTTI GLI UTENTI'
	admin_commands[13] = 'CANCELLA TUTTI I BANNATI'

	def __init__(self):
		if log != "NO" : print "TelegramAccessCheck v0.8 ..."
		if os.path.exists(self.user_file):
			with open(self.user_file) as json_file:
				json_data=json.load(json_file)
				self.user_ids=json_data[0]
				self.user_first_names=json_data[1]
				self.user_last_names=json_data[2]
				self.user_nicks=json_data[3]
				
		if os.path.exists(self.ban_user_file):
			with open(self.ban_user_file) as json_file_ban:
				json_data_ban=json.load(json_file_ban)
				self.ban_user_ids=json_data_ban[0]
				self.ban_user_first_names=json_data_ban[1]
				self.ban_user_last_names=json_data_ban[2]
				self.ban_user_nicks=json_data_ban[3]
				
	def save_user_list(self):
		user_data=[self.user_ids,self.user_first_names,self.user_last_names,self.user_nicks]
		with open(self.user_file, 'w') as outfile:
			json.dump(user_data, outfile,indent=4)
	
	def save_ban_user_list(self):
		user_ban_data=[self.ban_user_ids,self.ban_user_first_names,self.ban_user_last_names,self.ban_user_nicks]
		with open(self.ban_user_file, 'w') as outfileban:
			json.dump(user_ban_data, outfileban,indent=4)
	
	#Controlla se l'utente e' uno user autorizzato
	def user(self,bot,update):
		#Se non c'e' lista di utenti il primo che accede diventa admin
		if len(self.user_ids)==0:
			self.user_ids+=[update.message.from_user.id]
			self.user_first_names+=[update.message.from_user.first_name]
			self.user_last_names+=[update.message.from_user.last_name]
			self.user_nicks+=[update.message.from_user.username]
			self.save_user_list()
			if log != "NO" :
				print "-> Primo Accesso!!"
				print " {0} {1} {2} {3} diventa ADMIN".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			usr = "admin" 
			nickadmin = self.user_nicks[0]
			return (usr,nickadmin)

		#Se lo user e' in lista nella posizione 0 ritorna admin
		if self.user_ids[0]==update.message.from_user.id:
			if log != "NO" : print "-> Interazione dal ADMIN"
			usr = "admin" 
			nickadmin = self.user_nicks[0]
			return (usr,nickadmin)

		#Se lo user e' in lista torna "user"
		try:
			self.user_ids.index(update.message.from_user.id)
			if log != "NO" : print "-> Interazione da USER id:{0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			usr = "user" 
			nickadmin = self.user_nicks[0]
			return (usr,nickadmin)
			
		#Se non lo e' inoltra la richiesta d'accesso al admin
		except ValueError:
			try: 
				index_self_ban_id=self.ban_user_ids.index(update.message.from_user.id)
				if log != "NO" : print " Tentativo di Accesso da utente bannato! id:{0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
				bot.sendMessage(self.ban_user_ids[index_self_ban_id], "<i>Sei presente nella BlackList!</i>", parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				usr = "none"
				nickadmin = self.user_nicks[0]
				return (usr,nickadmin)
				
			except ValueError:
				if update.message.text not in admin_commands :
					index_self_ban_id=-1
					if log != "NO" : print "--> Nuovo Utente"
					auth_user_id = update.message.from_user.id
					chat_state = state.get(auth_user_id, AWAIT_INPUT)
					
					if log == "DEBUG" : 
						print " state.items: %s" % state.items()
						print " auth_user_id: %s" % auth_user_id
						print " chat_state: %s" % chat_state

					if chat_state == AWAIT_INPUT:
						state[auth_user_id] = AWAIT_CONFIRMATION
						
						# Save first_name, last_name,username for user id 
						tmp_first_name[auth_user_id] = update.message.from_user.first_name
						tmp_last_name[auth_user_id] = update.message.from_user.last_name
						tmp_username[auth_user_id] = update.message.from_user.username
						
						if log == "DEBUG" : 
							print " state.items AWAIT_CONFIRMATION: %s" % state.items()
							print " state[auth_user_id]: %s" % state[auth_user_id]				
							print " tmp_first_name[auth_user_id]: %s" % tmp_first_name[auth_user_id]
							print " tmp_last_name[auth_user_id]: %s" % tmp_last_name[auth_user_id]
							print " tmp_username[auth_user_id]: %s" % tmp_username[auth_user_id]
							print " tmp_first_name.items: %s" % tmp_first_name.items()
							print " tmp_last_name.items: %s" % tmp_last_name.items()
							print " tmp_username.items: %s" % tmp_username.items()
						
						bot.sendMessage(auth_user_id, "Richiesta di autorizzazione inviata all'amministratore.\nAttendere..." )
						
						yes_auth_user_id="YES_USER_AUTH--%s" % update.message.from_user.id
						no_auth_user_id="NO__USER_AUTH--%s" % update.message.from_user.id
						
						reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(YES_USER_AUTH, callback_data=yes_auth_user_id), InlineKeyboardButton(NO__USER_AUTH, callback_data=no_auth_user_id)]])
						contact_tmp = ['',"@{0}".format(tmp_username[auth_user_id])][tmp_username[auth_user_id] != '']
						bot.sendMessage(self.user_ids[0], "<b>%s %s</b> %s\n<i>Vorrebbe accedere al Bot</i>" % (tmp_first_name[auth_user_id],tmp_last_name[auth_user_id],contact_tmp), parse_mode=telegram.ParseMode.HTML, reply_markup=reply_markup)
					
					usr = "user_auth" 
					nickadmin = self.user_nicks[0]
					return (usr,nickadmin)
							
		#Negli altri casi nega l'accesso
		if log != "NO" : print "Accesso non autorizzato!"
		usr = "none"
		nickadmin = self.user_nicks[0]
		return (usr,nickadmin)

	def callbacks(self, bot, update):
		query = update.callback_query
		text = query.data
		callback_command = text[:15]
		user_command_id = int(text[15:])
		user_state = state.get(user_command_id, MENU)
		if log == "DEBUG" :
			print "---> callbacks"
			print " state.items: %s" % state.items()
			print " user_state: %s" % user_state
			print " query: %s" % query
			print " text:  %s" % text
			print " callback_command:  %s" % callback_command
			print " user_command_id:  %s" % user_command_id
		
		# Check if we are waiting for confirmation and the right user answered
		if user_state == AWAIT_CONFIRMATION:
			if log != "NO" : print "-------> callbacks-AWAIT_CONFIRMATION"
			del state[user_command_id]
			del user_state
			
			bot.answerCallbackQuery(query.id, text="Ok!")
		
			"""
			Gestione NUOVO UTENTE
			"""
			if callback_command == "YES_USER_AUTH--": 
				if log != "NO" : print "----> callbacks - Conferma Nuovo Utente (YES)"	
				if log == "DEBUG" : 		
					print " state.items: %s" % state.items()
					print " query: %s" % query
					print " text:  %s" % text
					print " callback_command:  %s" % callback_command
					print " user_command_id:  %s" % user_command_id
					print " tmp_first_name.items: %s" % tmp_first_name.items()
					print " tmp_last_name.items: %s" % tmp_last_name.items()
					print " tmp_username.items: %s" % tmp_username.items()
					print " tmp_first_name[user_command_id]: " + tmp_first_name[user_command_id]
					print " tmp_last_name[user_command_id]: %s" % tmp_last_name[user_command_id]
					print " tmp_username[user_command_id]: %s" % tmp_username[user_command_id]
					
				try: 
					index_self_id=self.user_ids.index(user_command_id)
					if log == "DEBUG" : print "Utente esistente in Archivio (%s %s %s %s)" % (user_command_id, tmp_first_name[user_command_id], tmp_last_name[user_command_id],tmp_username[user_command_id])
				except ValueError:
					index_self_id=-1
					self.user_ids+=[user_command_id]
					self.user_first_names+=[tmp_first_name[user_command_id]]
					self.user_last_names+=[tmp_last_name[user_command_id]]
					self.user_nicks+=[tmp_username[user_command_id]]
					self.save_user_list()
					if log != "NO" : print "Nuovo utente salvato in File Archivio (%s %s %s %s)" % (user_command_id, tmp_first_name[user_command_id], tmp_last_name[user_command_id], tmp_username[user_command_id])
					bot.sendMessage(user_command_id, "%s <b>SEI STATO AUTORIZZATO!</b>" % YES_USER_AUTH, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
					contact_tmp = ['',"@{0}".format(tmp_username[user_command_id])][tmp_username[user_command_id] != '']
					bot.sendMessage(self.user_ids[0], "%s %s %s\n%s <b>AUTORIZZATO</b>" % (tmp_first_name[user_command_id], tmp_last_name[user_command_id], contact_tmp, YES_USER_AUTH), parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
					
				del tmp_first_name[user_command_id]
				del tmp_last_name[user_command_id]
				del tmp_username[user_command_id]
				
				if log == "DEBUG" :
					print " eliminati tmp_first_name[user_command_id], tmp_last_name[user_command_id], tmp_username[user_command_id]"
					print " tmp_first_name.items: %s" % tmp_first_name.items()
					print " tmp_last_name.items: %s" % tmp_last_name.items()
					print " tmp_username.items: %s" % tmp_username.items()
					
			if callback_command == "NO__USER_AUTH--":
				if log != "NO" : print "----> callbacks - Rifiuto Nuovo Utente (NO)"
				
				try: 
					index_self_id_blacklist=self.ban_user_ids.index(user_command_id)
					if log == "DEBUG" : print "Utente esistente in Banlist (%s %s %s %s)" % (user_command_id, tmp_first_name[user_command_id], tmp_last_name[user_command_id],tmp_username[user_command_id])
				except ValueError:
					index_self_id_blacklist=-1
					self.ban_user_ids+=[user_command_id]
					self.ban_user_first_names+=[tmp_first_name[user_command_id]]
					self.ban_user_last_names+=[tmp_last_name[user_command_id]]
					self.ban_user_nicks+=[tmp_username[user_command_id]]
					self.save_ban_user_list()
					if log != "NO" : print "Nuovo utente salvato in File Banlist (%s %s %s %s)" % (user_command_id, tmp_first_name[user_command_id], tmp_last_name[user_command_id], tmp_username[user_command_id])
					
					bot.sendMessage(user_command_id, "%s <b>NON SEI STATO AUTORIZZATO!</b>" % NO__USER_AUTH, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
					
					contact_tmp = ['',"@{0}".format(tmp_username[user_command_id])][tmp_username[user_command_id] != '']
					bot.sendMessage(self.user_ids[0], "%s %s %s\n%s <b>NON AUTORIZZATO</b>\n<i>Aggiunto alla BanList!</i>" % (tmp_first_name[user_command_id], tmp_last_name[user_command_id], contact_tmp, NO__USER_AUTH), parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				
				del tmp_first_name[user_command_id]
				del tmp_last_name[user_command_id]
				del tmp_username[user_command_id]
				
				if log == "DEBUG" :
					print " eliminati tmp_first_name[user_command_id], tmp_last_name[user_command_id], tmp_username[user_command_id]"
					print " tmp_first_name.items: %s" % tmp_first_name.items()
					print " tmp_last_name.items: %s" % tmp_last_name.items()
					print " tmp_username.items: %s" % tmp_username.items()
			
			"""
			Gestione Cancellazione Utente /deluser
			"""
			if callback_command == "DEL_USER-------":
				if log != "NO" : print "----> callbacks - Cancellazione Utente"
				
				index_user_command_id = self.user_ids.index(user_command_id)
				
				if log == "DEBUG" : 		
					print " state.items: %s" % state.items()
					print " index_user_command_id: %s" % index_user_command_id
				
				if self.user_ids.index(user_command_id) :
					text_del="Utente: {0} {1} {2}".format(self.user_first_names[index_user_command_id], self.user_last_names[index_user_command_id], self.user_nicks[index_user_command_id])
					del self.user_ids[index_user_command_id]
					del self.user_first_names[index_user_command_id]
					del self.user_last_names[index_user_command_id]
					del self.user_nicks[index_user_command_id]
					self.save_user_list()
					if log != "NO" : print text_del + " ELIMINATO"
					if log == "DEBUG" : print " text_del: %s" % text_del
					
					bot.sendMessage(self.user_ids[0], "%s\n<b>ELIMINATO!</b>" % text_del, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
			
			"""
			Gestione Cancellazione Utente Bannato /delban
			"""
			if callback_command == "DEL_BAN--------":
				if log != "NO" : print "----> callbacks - Cancellazione Utente Bannato"
				
				index_user_command_id = self.ban_user_ids.index(user_command_id)
				
				if log == "DEBUG" : 		
					print " state.items: %s" % state.items()
					print " index_user_command_id: %s" % index_user_command_id
					print " self.ban_user_ids.index(user_command_id): %s" % self.ban_user_ids.index(user_command_id)

				text_del="Utente Bannato: {0} {1} {2}".format(self.ban_user_first_names[index_user_command_id], self.ban_user_last_names[index_user_command_id], self.ban_user_nicks[index_user_command_id])
				del self.ban_user_ids[index_user_command_id]
				del self.ban_user_first_names[index_user_command_id]
				del self.ban_user_last_names[index_user_command_id]
				del self.ban_user_nicks[index_user_command_id]
				self.save_ban_user_list()
				if log != "NO" : print text_del + " ELIMINATO"
				if log == "DEBUG" : print " text_del: %s" % text_del
				
				bot.sendMessage(self.user_ids[0], "%s\n<b>ELIMINATO!</b>" % text_del, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)			
			
	def cmd_userslist(self, bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /userlist negato a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return
			
		if True:
			i = 0 
			adm='Amministratore:'
			usr='Autorizzati:'
			ban='Bannati:'
			message_listuser='<b>Lista Utenti:</b>\n'
			if log == "DEBUG" :  print " len(self.user_first_names): %s" % len(self.user_ids)	
			while i < len(self.user_ids): 
				if i == 0 :
					message_listuser += "<i>{0}</i>".format(adm)
					contact_tmp = ['',"@{0}".format(self.user_nicks[i])][self.user_nicks[i] != '']
					message_listuser += "\n  {0} {1} {2}".format(self.user_first_names[i], self.user_last_names[i], contact_tmp)
				elif i == 1 :
					message_listuser += "\n<i>{0}</i>".format(usr)
					contact_tmp = ['',"@{0}".format(self.user_nicks[i])][self.user_nicks[i] != '']
					message_listuser += "\n  {0} {1} {2}".format(self.user_first_names[i], self.user_last_names[i], contact_tmp)
				else :
					contact_tmp = ['',"@{0}".format(self.user_nicks[i])][self.user_nicks[i] != '']
					message_listuser += "\n  {0} {1} {2}".format(self.user_first_names[i], self.user_last_names[i], contact_tmp)
				i = i + 1 
				
			if log == "DEBUG" :  print " len(self.ban_user_ids): %s" % len(self.ban_user_ids)	
			i = 0 
			while i < len(self.ban_user_ids): 
				if i == 0 :
					message_listuser += "\n<i>{0}</i>".format(ban)
					contact_tmp = ['',"@{0}".format(self.ban_user_nicks[i])][self.ban_user_nicks[i] != '']
					message_listuser += "\n  {0} {1} {2}".format(self.ban_user_first_names[i], self.ban_user_last_names[i], contact_tmp)
				else :
					contact_tmp = ['',"@{0}".format(self.ban_user_nicks[i])][self.ban_user_nicks[i] != '']
					message_listuser += "\n  {0} {1} {2}".format(self.ban_user_first_names[i], self.ban_user_last_names[i], contact_tmp)
				i = i + 1 
			if log == "DEBUG" :  print " message_listuser: %s" % message_listuser		
			bot.sendMessage(update.message.chat_id, message_listuser, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
			if log != "NO" : print "Visualizzata lista utenti %s e ban %s" % (self.user_ids, self.ban_user_ids)
		else:
			if log != "NO" : print "Comando non Autorizzato!"
	
	def cmd_users(self, bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /users negato  a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return
			
		if True:
			if len(self.user_ids) > 1 :
				i = 1
				titolo='Lista Utenti Autorizzati: '+YES_USER_AUTH
				message_userlist=''
				if log == "DEBUG" :  print " len(self.user_ids): %s" % len(self.user_ids)	
				while i < len(self.user_ids): 
					if i == 1 :
						message_userlist += "<b>%s</b>" % titolo
						contact_tmp = ['',"@{0}".format(self.user_nicks[i])][self.user_nicks[i] != '']
						message_userlist += "\n  {0} {1} {2}".format(self.user_first_names[i], self.user_last_names[i], contact_tmp)
					else :
						contact_tmp = ['',"@{0}".format(self.user_nicks[i])][self.user_nicks[i] != '']
						message_userlist += "\n  {0} {1} {2}".format(self.user_first_names[i], self.user_last_names[i], contact_tmp)
					i = i + 1 
				if log == "DEBUG" :  print " message_userlist: %s" % message_userlist		
				bot.sendMessage(update.message.chat_id, message_userlist, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				if log != "NO" : print "Visualizzata lista utenti autorizzati " , self.user_ids[1:]
			else :
				bot.sendMessage(update.message.chat_id, "<b>Lista Utenti Autorizzati:</b> "+YES_USER_AUTH+"\n<i>NON CI SONO UTENTI AUTORIZZATI!</i>", parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				if log != "NO" : print "Richiesta /users ma vuota " , self.user_ids[1:]
		else:
			if log != "NO" : print "Comando non Autorizzato!"
	
	def cmd_bans(self, bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /bans negato a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return
		if True:
			if len(self.ban_user_ids) > 0 :
				i = 0 
				titolo='Lista Utenti Bannati: '+NO__USER_AUTH
				message_banlist=''
				if log == "DEBUG" :  print " len(self.ban_user_ids): %s" % len(self.ban_user_ids)	
				while i < len(self.ban_user_ids): 
					if i == 0 :
						message_banlist += "<b>%s</b>" % titolo
						contact_tmp = ['',"@{0}".format(self.ban_user_nicks[i])][self.ban_user_nicks[i] != '']
						message_banlist += "\n  {0} {1} {2}".format(self.ban_user_first_names[i], self.ban_user_last_names[i], contact_tmp)
					else :
						contact_tmp = ['',"@{0}".format(self.ban_user_nicks[i])][self.ban_user_nicks[i] != '']
						message_banlist += "\n  {0} {1} {2}".format(self.ban_user_first_names[i], self.ban_user_last_names[i], contact_tmp)
					i = i + 1 
				if log == "DEBUG" :  print " message_banlist: %s" % message_banlist		
				bot.sendMessage(update.message.chat_id, message_banlist, parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				if log != "NO" : print "Visualizzata lista utenti bannati " , self.ban_user_ids
			else:
				bot.sendMessage(update.message.chat_id, "<b>Lista Utenti Bannati:</b> "+NO__USER_AUTH+"\n<i>NON CI SONO UTENTI BANNATI!</i>", parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				if log != "NO" : print "Richiesta /bans ma vuota " , self.ban_user_ids
		else:
			if log != "NO" : print "Comando non Autorizzato!"
	
	def cmd_deluser(self, bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /deluser negato a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return
			
		if True:
			if log == "DEBUG" :  
					# print " custom_inline_keyboard: %s" % custom_inline_keyboard	
					print " state.items: %s" % state.items()
					
			if len(self.user_ids) > 1 :
				custom_inline_keyboard = []
				i = 0
				for user in self.user_ids:
					if user != self.user_ids[0] :
						ikb = InlineKeyboardButton(text='{0}. {1} {2} {3}'.format(i,self.user_first_names[i],self.user_last_names[i],self.user_nicks[i]), callback_data='DEL_USER-------'+str(user))
						custom_inline_keyboard.append([ikb])
						state[user] = AWAIT_CONFIRMATION
					i=i+1
				reply_markup_del = InlineKeyboardMarkup(custom_inline_keyboard)
				
				if log == "DEBUG" :  
					# print " custom_inline_keyboard: %s" % custom_inline_keyboard	
					print " state.items: %s" % state.items()
					print " reply_markup_del: %s" % reply_markup_del
					
				
				bot.sendMessage(self.user_ids[0], "<i>Selezionare l'utente da Eliminare:</i>", parse_mode=telegram.ParseMode.HTML, reply_markup=reply_markup_del)			
				if log != "NO" : print "Visualizzata lista utenti da eliminare " , self.user_ids[1:]
			else :
				bot.sendMessage(update.message.chat_id, "<b>Non sono presenti utenti da eliminare!</b>", parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				if log != "NO" : print "Richiesta /delusers ma non sono presenti utenti da eliminare " , self.user_ids[1:]
		else:
			if log != "NO" : print "Comando non Autorizzato!"
			
	def cmd_delban(self, bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /delban negato a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return
			
		if True:
			if log == "DEBUG" :  
					# print " custom_inline_keyboard: %s" % custom_inline_keyboard	
					print " state.items: %s" % state.items()
					
			if len(self.ban_user_ids) > 0 :
				custom_inline_keyboard = []
				i = 0
				
				for user in self.ban_user_ids:
					ikb = InlineKeyboardButton(text='{0}. {1} {2} {3}'.format(i+1,self.ban_user_first_names[i],self.ban_user_last_names[i],self.ban_user_nicks[i]), callback_data='DEL_BAN--------'+str(user))
					custom_inline_keyboard.append([ikb])
					state[user] = AWAIT_CONFIRMATION
					i=i+1
				reply_markup_del = InlineKeyboardMarkup(custom_inline_keyboard)
				
				if log == "DEBUG" :  
					# print " custom_inline_keyboard: %s" % custom_inline_keyboard	
					print " state.items: %s" % state.items()
					print " reply_markup_del: %s" % reply_markup_del
					
				
				bot.sendMessage(self.user_ids[0], "<i>Selezionare l'utente bannato da Eliminare:</i>", parse_mode=telegram.ParseMode.HTML, reply_markup=reply_markup_del)			
				if log != "NO" : print "Visualizzata lista utenti bannati da eliminare " , self.ban_user_ids[0:]
			else :
				bot.sendMessage(self.user_ids[0], "<b>Non sono presenti utenti bannati da eliminare!</b>", parse_mode=telegram.ParseMode.HTML, reply_markup=clear_keyboard)
				if log != "NO" : print "Richiesta /delusers ma non sono presenti utenti bannati da eliminare " , self.ban_user_ids[0:]
		else:
			if log != "NO" : print "Comando non Autorizzato!"
	
	def cmd_delallusers(self,bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /delallusers negato a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return

		if True:
			del self.user_ids[1:]
			del self.user_first_names[1:]
			del self.user_last_names[1:]
			del self.user_nicks[1:]
			self.save_user_list()
			bot.sendMessage(update.message.chat_id, "Cancellati tutti gli user", reply_markup=clear_keyboard)
			if log != "NO" : print "Cancellati tutti gli user"
		else:
			if log != "NO" : print "Comando non autorizzato"
		
		if log != "NO" : print "Lista utenti autorizzati" , self.user_ids[1:]
	
	def cmd_delallbans(self,bot, update):
		if self.user(bot,update)[0]!="admin":
			if log != "NO" : print "Accesso al comando /delallbans negato a user: id {0} - {1} {2} {3}".format(update.message.from_user.id, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.username)
			bot.sendMessage(update.message.chat_id, NO_ENTRY+" Accesso al comando non autorizzato!", reply_markup=clear_keyboard)
			return

		if True:
			del self.ban_user_ids[0:]
			del self.ban_user_first_names[0:]
			del self.ban_user_last_names[0:]
			del self.ban_user_nicks[0:]
			self.save_ban_user_list()
			bot.sendMessage(update.message.chat_id, "Cancellati tutti i ban", reply_markup=clear_keyboard)
			if log != "NO" : print "Cancellati tutti i ban"
		else:
			if log != "NO" : print "Comando non autorizzato"
		
		if log != "NO" : print "Lista utenti bannati" , self.ban_user_ids

	def addAccessCheckCommandHandler(self,dispatcher):
		dispatcher.add_handler(CallbackQueryHandler(self.callbacks))
		dispatcher.add_handler(CommandHandler("userslist",self.cmd_userslist))
		dispatcher.add_handler(CommandHandler("users",self.cmd_users))
		dispatcher.add_handler(CommandHandler("bans",self.cmd_bans))
		dispatcher.add_handler(CommandHandler("deluser",self.cmd_deluser))
		dispatcher.add_handler(CommandHandler("delban",self.cmd_delban))
		dispatcher.add_handler(CommandHandler("delallusers",self.cmd_delallusers))
		dispatcher.add_handler(CommandHandler("delallbans",self.cmd_delallbans))