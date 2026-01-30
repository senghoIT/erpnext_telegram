# -*- coding: utf-8 -*-
# Copyright (c) 2019, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import os
import frappe
import telegram
import asyncio
from frappe.model.document import Document
from frappe.utils import get_url_to_form
from frappe.utils.data import quoted
from frappe import _
from bs4 import BeautifulSoup
from frappe.utils.file_manager import get_file_path


class TelegramSettings(Document):
	pass



@frappe.whitelist()
def send_to_telegram(telegram_user, message, reference_doctype=None, reference_name=None, attachment=None,show_link=False):

	space = "\n" * 2
	telegram_chat_id = frappe.db.get_value('Telegram User Settings', telegram_user,'telegram_chat_id')
	telegram_settings = frappe.db.get_value('Telegram User Settings', telegram_user,'telegram_settings')
	telegram_token = frappe.db.get_value('Telegram Settings', telegram_settings,'telegram_token')
	bot = telegram.Bot(token=telegram_token)


	if reference_doctype and reference_name:
		if show_link:
			doc_url = get_url_to_form(reference_doctype, reference_name)
			telegram_doc_link = _("See the document at {0}").format(doc_url)
		if message:
			soup = BeautifulSoup(message)
			if show_link:
				message = soup.get_text('\n') + space + str(telegram_doc_link)
			message = soup.get_text('\n')
			if type(attachment) is str:
				attachment = int(attachment)
			else:
				if attachment:
					attachment = 1
			if attachment == 1:
				attachment_url =get_url_for_telegram(reference_doctype, reference_name)
				message = message + space +  attachment_url
			try:
				loop = asyncio.get_running_loop()
			except RuntimeError:
				loop = None
			
			if loop and loop.is_running():
				# loop.create_task(send_to_telegram_async(bot=bot,telegram_chat_id=telegram_chat_id,message=message,reference_doctype=reference_doctype,reference_name=reference_name))
				loop.create_task(bot.send_message(chat_id=telegram_chat_id, text=message))
				
			else:
				asyncio.run(bot.send_message(chat_id=telegram_chat_id, text=message))

		else:
			message = space + str(message) + space


@frappe.whitelist()
def send_image_to_telegram(telegram_user, message, reference_doctype=None, reference_name=None, attachment=None,send_location=0):
	
	telegram_chat_id = frappe.db.get_value('Telegram User Settings', telegram_user,'telegram_chat_id')
	telegram_settings = frappe.db.get_value('Telegram User Settings', telegram_user,'telegram_settings')
	telegram_token = frappe.db.get_value('Telegram Settings', telegram_settings,'telegram_token')
	bot = telegram.Bot(token=telegram_token)

	if reference_doctype and reference_name:
		if message:
			soup = BeautifulSoup(message)
			message = soup.get_text('\n')
			doc = frappe.get_doc(reference_doctype, reference_name)
			try:
				loop = asyncio.get_running_loop()
			except RuntimeError:
				loop = None
			file_doc = frappe.get_doc("File", {"attached_to_doctype": reference_doctype, "attached_to_name": reference_name})
			file_path = file_doc.get_full_path()
			if loop and loop.is_running():
				async def send_async():
					with open(file_path, 'rb') as photo_file:
						try:
							await bot.send_photo(chat_id=telegram_chat_id, photo=photo_file, caption=message,read_timeout=60,
                write_timeout=60, 
                connect_timeout=30)
							if send_location == 1:
								await bot.send_location(chat_id=telegram_chat_id,latitude=doc.latitude,longitude=doc.longitude)
						except Exception as e:
							await bot.send_message(chat_id=telegram_chat_id, text=f"{message}\n {e}")
							frappe.log_error(f"Telegram Send Error: {e}")
				loop.create_task(send_async())
			else:
				if os.path.exists(file_path):
					with open(file_path, 'rb') as photo_file:
						try:
							asyncio.run(bot.send_photo(chat_id=telegram_chat_id,
								photo=photo_file,caption=f"{message}",read_timeout=60,
                				write_timeout=60, 
                				connect_timeout=30)
								)
							if send_location == 1:
								asyncio.run(bot.send_location(chat_id=telegram_chat_id,latitude=doc.latitude,longitude=doc.longitude))
						except Exception as e:
							asyncio.run(bot.send_message(
								chat_id=telegram_chat_id, 
								text=f"{message}\n {e}" 
							))
							frappe.log_error(f"Telegram Send Error: {e}")
		
@frappe.whitelist()
def send_location_to_telegram(telegram_user, message, reference_doctype=None, reference_name=None,lat='latitude',long='longitude'):

	space = "\n" * 2
	telegram_chat_id = frappe.db.get_value('Telegram User Settings', telegram_user,'telegram_chat_id')
	telegram_settings = frappe.db.get_value('Telegram User Settings', telegram_user,'telegram_settings')
	telegram_token = frappe.db.get_value('Telegram Settings', telegram_settings,'telegram_token')
	bot = telegram.Bot(token=telegram_token)


	if reference_doctype and reference_name:
		if message:
			soup = BeautifulSoup(message)
			message = soup.get_text('\n')
			doc = frappe.get_doc(reference_doctype, reference_name)
			try:
				loop = asyncio.get_running_loop()
			except RuntimeError:
				loop = None
			if loop and loop.is_running():
				# loop.create_task(send_to_telegram_async(bot=bot,telegram_chat_id=telegram_chat_id,message=message,reference_doctype=reference_doctype,reference_name=reference_name))
				loop.create_task(bot.send_location(chat_id=telegram_chat_id,latitude=doc.get(lat),longitude=doc.get(long)))
			else:
				asyncio.run(bot.send_location(chat_id=telegram_chat_id,latitude=doc.get(lat),longitude=doc.get(long)))
		else:
			message = space + str(message) + space



def get_url_for_telegram(doctype, name):
	doc = frappe.get_doc(doctype, name)
	return "{url}/api/method/erpnext_telegram_integration.get_pdf.pdf?doctype={doctype}&name={name}&key={key}".format(
		url=frappe.utils.get_url(),
		doctype=quoted(doctype),
		name=quoted(name),
		key=doc.get_signature()
	)


