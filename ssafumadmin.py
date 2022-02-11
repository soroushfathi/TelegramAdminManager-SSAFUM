import re
import os
import sched
import time
from datetime import datetime, timezone, timedelta

from telethon.errors.rpcerrorlist import(
    MessageAuthorRequiredError,
    ChatIdInvalidError,
    MessageIdInvalidError,
)
from telethon import (
    TelegramClient,
    events,
)
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import (
    PeerChannel,
    PeerUser,
    PeerChat,
)

api_id = os.environ["SSAFUM_apiID"]
api_hash = os.environ["SSAFUM_apiHASH"]
client = TelegramClient('main', api_id, api_hash)


channels = []  # (channel id, channel link, channel title)
main_channel = {
    'id': 1005121326,
    'title': 'انجمن های علمی فردوسی مشهد',
}
main_group = {
    'id': 1751972489,
    'title': 'SSA FUM Admins',
}
keywords = []  # keywords: if the post include added keywords, won't be sent to the admins group


@client.on(events.NewMessage)
async def my_event_handler(event):
    if re.match(r'(?i).*(hello)$', event.raw_text, re.IGNORECASE):
        user = PeerUser((await event.message.get_sender()).id)
        user = await client.get_entity(user)
        await event.reply('Hi {}👋🏻, I\'m Admin of Student Science Association Ferdowsi University of mashhad, '
                          '@soroush_fathi programmed me to do this job🤠'.format(user.first_name))


@client.on(events.NewMessage)
async def commands(event):
    strs = event.raw_text.split('\n')
    try:
        chat = await client.get_entity(PeerChat((await event.message.get_chat())).chat_id)
        # Admins can just use these commands(events from SSA FUM Admins)
        if chat.id == main_group['id']:
            # add channels: join the given channels and send there post for admins
            if re.findall(r'(?i)add[ ]*channel[s]?$', event.raw_text):
                if len(strs) == 1:
                    await event.reply('لیست کانال ها برای افزودن خالی است🙂')
                else:
                    tmp = await event.reply('⏳در حال بررسی کانال ها ...')
                    res = ''
                    async with client.action(chat, 'typing'):
                        for i, item in zip(range(len(strs)), strs[:len(strs) - 1]):
                            if item[0] == '@':
                                item = item[1:]
                            try:
                                channel = await client.get_entity(item)
                                if await client(JoinChannelRequest(channel)):
                                    res += '✅عضویت کانال {}({}ام): موفق'.format(channel.title, i + 1) + '\n'
                                if re.findall(r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+', item):
                                    channels.append((channel.id, item, channel.title))
                                else:
                                    channels.append((channel.id, 'https://t.me/' + item, channel.title))
                            except ValueError:
                                res += '❌عضویت کانال {}ام: ناموفق(کانالی با این نشانی برای عضویت وجود ندارد)\n'.format(
                                    i+1)
                            except TypeError:
                                res += '❌عضویت کانال {}ام: ناموفق(برای ورودی فقط آدرس کانال را وارد کنید)\n'.format(i+1)
                await client.delete_messages(chat, tmp)
                await client.send_message(chat, res, reply_to=event.message)
            elif re.findall(r'(?i)remove[ ]*channel[s]?$', event.raw_text):
                if len(strs) == 1:
                    await event.reply('لیست کانال ها برای ترک کردن خالی است🙂')
                else:
                    res = ''
                    for i, item in zip(range(len(strs)), strs[:len(strs) - 1]):
                        try:
                            channel = await client.get_entity(item)
                            if await client(LeaveChannelRequest(channel)):
                                res += '✅ترک کانال {}({}ام): موفق'.format(channel.title, i + 1) + '\n'
                            if re.findall(r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+', item):
                                channels.remove((channel.id, item, channel.title))
                            else:
                                channels.remove((channel.id, 'https://t.me/' + item, channel.title))
                        except ValueError:
                            res += '❌ترک کانال {}ام: ناموفق(کانالی با این نشانی برای ترک وجود ندارد)\n'.format(i + 1)
                        except TypeError:
                            res += '❌ترک کانال {}ام: ناموفق(برای ورودی فقط آدرس کانال را وارد کنید)\n'.format(i + 1)
                await event.reply(res)
            elif re.findall(r'(?i)add[ ]*keyword[s]$', event.raw_text):
                for kw in strs[:len(strs) - 1]:
                    keywords.append(kw)
                await event.reply('✅کليد واژه های مورد نظر با موفقیت اضافه شد')
            elif re.findall(r'(?i)remove[ ]*keywords$', event.raw_text):
                for kw in strs[:len(strs) - 1]:
                    keywords.remove(kw)
                await event.reply('✅کليد واژه های مورد نظر با موفقیت حذف شد')
            elif re.findall(r'(?i).*channel[s]?[ ]*list$', event.raw_text):
                lc = len(channels)
                if lc == 0:
                    await event.reply('لیست کانال های مورد بررسی خالی است')
                else:
                    try:
                        if lc <= 30:
                            await event.reply(' 🟢\n'.join([str(x[1]) + ': ' + str(x[2]) for x in channels]) + ' 🟢')
                        else:
                            for i in range(lc//30 + 1):
                                await event.reply(
                                    ' 🟢\n'.join([str(x[1]) + ': ' + str(x[2]) for x in
                                                  channels[30*i:30*(i+1) if 30*(i+1) <= lc else lc]])+' 🟢'
                                )
                    except telethon.errors.rpcerrorlist.FloodWaitError:
                        await event.reply('تلاش ناموفق، دوباره امتحان کنید')
                    except telethon.errors.FloodError:
                        await event.reply('تلاش ناموفق، دوباره امتحان کنید')
            elif re.findall(r'(?i).*keyword[s]?[ ]*list$', event.raw_text):
                if len(keywords) == 0:
                    await event.reply('لیست کلید واژه ها خالی است')
                else:
                    try:
                        async with client.action(chat, 'typing'):
                            await event.reply(' 🟢\n'.join([str(x) for x in keywords]) + ' 🟢')
                    except telethon.errors.FloodError:
                        await event.reply('تلاش ناموفق، دوباره امتحان کنید')
    except ChatIdInvalidError:
        pass
    except AttributeError:
        await event.reply('❗️access out of bounds🙂 \n'
                          '🚫شما در این محدوده مجاز به استفاده از دستورات نمی باشید. با تشکر')


@client.on(events.Album)
async def new_album_post(event):
    print(event)
    await client.forward_messages(main_group['id'], event.messages)


@client.on(events.NewMessage(forwards=False))
async def new_post(event):
    await post_analyser(event)


@client.on(events.MessageEdited(forwards=False))
async def new_edited_post(event):
    await post_analyser(event)


# check if post has not contain a given keywords and from channel that have been added
async def post_analyser(event):
    try:
        ch = PeerChannel((await event.message.get_sender()).id)
        ch = await client.get_entity(ch)
        keyflag = True
        for i in keywords:
            if i in event.raw_text:
                keyflag = False
                break
        if not re.findall(r'(?i)ssafum', event.raw_text):
            keyflag = False
        if ch.id in [item[0] for item in channels] and keyflag:
            await client.forward_messages(main_group['id'], event.message, as_album=True)
    except ValueError:
        pass


@client.on(events.NewMessage)
async def post_archives(event):
    chat = await client.get_entity(PeerChat((await event.message.get_chat())).chat_id)
    if re.findall(r'(?i).*accept$', event.raw_text) and chat.id == main_group['id']:
        # get the date of last message, if now - date < 10min --> send with schedule
        lastmsgs = []
        channel = await client.get_entity('ssafum')
        async for item in client.iter_messages(main_channel['id'], scheduled=True):
            lastmsgs.append(item)
            break
        if len(lastmsgs) == 0:
            async for item in client.iter_messages(main_channel['id']):
                lastmsgs.append(item)
                break
        minutes_diff = (datetime.now(timezone.utc) - lastmsgs[0].date).total_seconds() // 60
        try:
            if minutes_diff >= 10:
                msg = await client.get_messages(chat, ids=event.reply_to_msg_id)
                if await client.forward_messages(main_channel['id'], msg):
                    await event.reply('ارسال با موفقیت انجام شد📤')
                    # await client.edit_message(chat, msg, '✔️این پست قبلا تایید گردیده است')
                    # await client.delete_messages(chat, msg)
            else:
                msg = await client.get_messages(chat, ids=event.reply_to_msg_id)
                if await client.forward_messages(main_channel['id'], msg, schedule=timedelta(minutes=10 - int(minutes_diff))):
                    await event.reply('✔️پست {} دقیقه دیگر ارسال می شود 📤'.format(10 - int(minutes_diff)))
                    # await client.ediِt_message(chat, msg, '✔️این پست قبلا تایید گردیده است')
                    # await client.delete_messages(chat, msg)
        except MessageAuthorRequiredError:
            pass
        except MessageIdInvalidError:
            pass
    elif re.findall(r'(?i).*ignore$', event.raw_text) and chat.id == main_group['id']:
        try:
            msg = await client.get_messages(chat, ids=event.reply_to_msg_id)
            await event.reply('عدم تایید 🛑 حذف پست انجام شد🗑')
            # await client.edit_message(chat, msg, '❌این پست قبلا حذف گردیده است📫')
            await client.delete_messages(chat, msg)
        except MessageAuthorRequiredError:
            pass
        except MessageIdInvalidError:
            pass


client.start()
client.run_until_disconnected()
