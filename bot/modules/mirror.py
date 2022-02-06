import requests

from re import match, search, split as resplit
from time import sleep, time
from os import path as ospath, remove as osremove, listdir, walk
from shutil import rmtree
from threading import Thread
from subprocess import run as srun
from pathlib import PurePath
from urllib.parse import quote
from telegram.ext import CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot import Interval, INDEX_URL, BUTTON_FOUR_NAME, BUTTON_FOUR_URL, BUTTON_FIVE_NAME, BUTTON_FIVE_URL, \
                BUTTON_SIX_NAME, BUTTON_SIX_URL, BLOCK_MEGA_FOLDER, BLOCK_MEGA_LINKS, VIEW_LINK, aria2, QB_SEED, \
                dispatcher, DOWNLOAD_DIR, download_dict, download_dict_lock, TG_SPLIT_SIZE, LOGGER, BOT_PM
from bot.helper.ext_utils.bot_utils import get_readable_file_size, is_url, is_magnet, is_gdtot_link, is_mega_link, is_gdrive_link, get_content_type, get_mega_link_type
from bot.helper.ext_utils.fs_utils import get_base_name, get_path_size, split as fssplit, clean_download
from bot.helper.ext_utils.shortenurl import short_url
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException, NotSupportedExtractionArchive
from bot.helper.mirror_utils.download_utils.aria2_download import add_aria2c_download
from bot.helper.mirror_utils.download_utils.mega_downloader import add_mega_download
from bot.helper.mirror_utils.download_utils.gd_downloader import add_gd_download
from bot.helper.mirror_utils.download_utils.qbit_downloader import add_qb_torrent
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator
from bot.helper.mirror_utils.download_utils.telegram_downloader import TelegramDownloadHelper
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.mirror_utils.status_utils.tg_upload_status import TgUploadStatus
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.mirror_utils.upload_utils.pyrogramEngine import TgUploader
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, delete_all_messages, update_all_messages, sendLog, sendPrivate, sendtextlog, editMessage
from bot.helper.telegram_helper.button_build import ButtonMaker


class MirrorListener:
    def __init__(self, bot, update, isZip=False, extract=False, isQbit=False, isLeech=False, pswd=None, tag=None):
        self.bot = bot
        self.update = update
        self.message = update.message
        self.uid = self.message.message_id
        self.extract = extract
        self.isZip = isZip
        self.isQbit = isQbit
        self.isLeech = isLeech
        self.pswd = pswd
        self.tag = tag

    def clean(self):
        try:
            aria2.purge()
            Interval[0].cancel()
            del Interval[0]
            delete_all_messages()
        except IndexError:
            pass

    def onDownloadComplete(self):
        with download_dict_lock:
            LOGGER.info(f"Download completed: {download_dict[self.uid].name()}")
            download = download_dict[self.uid]
            name = str(download.name()).replace('/', '')
            gid = download.gid()
            size = download.size_raw()
            if name == "None" or self.isQbit:
                name = listdir(f'{DOWNLOAD_DIR}{self.uid}')[-1]
            m_path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        if self.isZip:
            try:
                with download_dict_lock:
                    download_dict[self.uid] = ZipStatus(name, m_path, size)
                pswd = self.pswd
                path = m_path + ".zip"
                LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
                if pswd is not None:
                    if self.isLeech and int(size) > TG_SPLIT_SIZE:
                        path = m_path + ".zip"
                        srun(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{pswd}", path, m_path])
                    else:
                        srun(["7z", "a", "-mx=0", f"-p{pswd}", path, m_path])
                elif self.isLeech and int(size) > TG_SPLIT_SIZE:
                    path = m_path + ".zip"
                    srun(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, m_path])
                else:
                    srun(["7z", "a", "-mx=0", path, m_path])
            except FileNotFoundError:
                LOGGER.info('File to archive not found!')
                self.onUploadError('Internal error occurred!!')
                return
            try:
                rmtree(m_path, ignore_errors=True)
            except:
                osremove(m_path)
        elif self.extract:
            try:
                if ospath.isfile(m_path):
                    path = get_base_name(m_path)
                LOGGER.info(f"Extracting: {name}")
                with download_dict_lock:
                    download_dict[self.uid] = ExtractStatus(name, m_path, size)
                pswd = self.pswd
                if ospath.isdir(m_path):
                    for dirpath, subdir, files in walk(m_path, topdown=False):
                        for file_ in files:
                            if search(r'\.part0*1.rar$', file_) or search(r'\.7z.0*1$', file_) \
                               or (file_.endswith(".rar") and not search(r'\.part\d+.rar$', file_)) \
                               or file_.endswith(".zip") or search(r'\.zip.0*1$', file_):
                                m_path = ospath.join(dirpath, file_)
                                if pswd is not None:
                                    result = srun(["7z", "x", f"-p{pswd}", m_path, f"-o{dirpath}", "-aot"])
                                else:
                                    result = srun(["7z", "x", m_path, f"-o{dirpath}", "-aot"])
                                if result.returncode != 0:
                                    LOGGER.error('Unable to extract archive!')
                        for file_ in files:
                            if file_.endswith(".rar") or search(r'\.r\d+$', file_) \
                               or search(r'\.7z.\d+$', file_) or search(r'\.z\d+$', file_) \
                               or search(r'\.zip.\d+$', file_) or file_.endswith(".zip"):
                                del_path = ospath.join(dirpath, file_)
                                osremove(del_path)
                    path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
                else:
                    if pswd is not None:
                        result = srun(["bash", "pextract", m_path, pswd])
                    else:
                        result = srun(["bash", "extract", m_path])
                    if result.returncode == 0:
                        LOGGER.info(f"Extract Path: {path}")
                        osremove(m_path)
                        LOGGER.info(f"Deleting archive: {m_path}")
                    else:
                        LOGGER.error('Unable to extract archive! Uploading anyway')
                        path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        else:
            path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        up_name = PurePath(path).name
        up_path = f'{DOWNLOAD_DIR}{self.uid}/{up_name}'
        size = get_path_size(f'{DOWNLOAD_DIR}{self.uid}')
        if self.isLeech and not self.isZip:
            checked = False
            for dirpath, subdir, files in walk(f'{DOWNLOAD_DIR}{self.uid}', topdown=False):
                for file_ in files:
                    f_path = ospath.join(dirpath, file_)
                    f_size = ospath.getsize(f_path)
                    if int(f_size) > TG_SPLIT_SIZE:
                        if not checked:
                            checked = True
                            with download_dict_lock:
                                download_dict[self.uid] = SplitStatus(up_name, up_path, size)
                            LOGGER.info(f"Splitting: {up_name}")
                        fssplit(f_path, f_size, file_, dirpath, TG_SPLIT_SIZE)
                        osremove(f_path)
        if self.isLeech:
            LOGGER.info(f"Leech Name: {up_name}")
            tg = TgUploader(up_name, self)
            tg_upload_status = TgUploadStatus(tg, size, gid, self)
            with download_dict_lock:
                download_dict[self.uid] = tg_upload_status
            update_all_messages()
            tg.upload()
        else:
            LOGGER.info(f"Upload Name: {up_name}")
            drive = GoogleDriveHelper(up_name, self)
            upload_status = UploadStatus(drive, size, gid, self)
            with download_dict_lock:
                download_dict[self.uid] = upload_status
            update_all_messages()
            drive.upload(up_name)

    def onDownloadError(self, error):
        error = error.replace('<', ' ')
        error = error.replace('>', ' ')
        with download_dict_lock:
            try:
                download = download_dict[self.uid]
                del download_dict[self.uid]
                clean_download(download.path())
            except Exception as e:
                LOGGER.error(str(e))
            count = len(download_dict)
        msg = f"{self.tag} your download has been stopped due to: {error}"
        sendMessage(msg, self.bot, self.update)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadComplete(self, link: str, size, files, folders, typ):
        if self.isLeech:
            if self.isQbit and QB_SEED:
                pass
            else:
                with download_dict_lock:
                    try:
                        clean_download(download_dict[self.uid].path())
                    except FileNotFoundError:
                        pass
                    del download_dict[self.uid]
                    dcount = len(download_dict)
                if dcount == 0:
                    self.clean()
                else:
                    update_all_messages()
            count = len(files)
            msg = f'𝗡𝗮𝗺𝗲: <code>{link}</code>\n\n'
            msg += f'𝗦𝗶𝘇𝗲: {get_readable_file_size(size)}\n'
            msg += f'𝗧𝗼𝘁𝗮𝗹 𝗙𝗶𝗹𝗲𝘀: {count}'
            if typ != 0:
                msg += f'\n𝗖𝗼𝗿𝗿𝘂𝗽𝘁𝗲𝗱 𝗙𝗶𝗹𝗲𝘀: {typ}'
            if self.message.chat.type == 'private':
                sendMessage(msg, self.bot, self.update)
            else:
                chat_id = str(self.message.chat.id)[4:]
                msg += f'\n𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝗬: {self.tag}\n\n'
                fmsg = ''
                for index, item in enumerate(list(files), start=1):
                    msg_id = files[item]
                    link = f"https://t.me/c/{chat_id}/{msg_id}"
                    fmsg += f"{index}. <a href='{link}'>{item}</a>\n"
                    if len(fmsg.encode('utf-8') + msg.encode('utf-8')) > 4000:
                        sleep(2)
                        sendMessage(msg + fmsg, self.bot, self.update)
                        fmsg = ''
                if fmsg != '':
                    sleep(2)
                    sendMessage(msg + fmsg, self.bot, self.update)
            return

        with download_dict_lock:
            msg = f'𝗡𝗮𝗺𝗲: <code>{download_dict[self.uid].name()}</code>\n\n𝗦𝗶𝘇𝗲: {size}'
            msg += f'\n\n𝗧𝘆𝗽𝗲: {typ}'
            if ospath.isdir(f'{DOWNLOAD_DIR}/{self.uid}/{download_dict[self.uid].name()}'):
                msg += f'\n𝗦𝘂𝗯𝗙𝗼𝗹𝗱𝗲𝗿𝘀: {folders}'
                msg += f'\n𝗙𝗶𝗹𝗲𝘀: {files}'
            buttons = ButtonMaker()
            link = short_url(link)
            buttons.buildbutton("☁️ 𝗗𝗿𝗶𝘃𝗲 𝗟𝗶𝗻𝗸", link)
            LOGGER.info(f'Done Uploading {download_dict[self.uid].name()}')
            if INDEX_URL is not None:
                url_path = requests.utils.quote(f'{download_dict[self.uid].name()}')
                share_url = f'{INDEX_URL}/{url_path}'
                if ospath.isdir(f'{DOWNLOAD_DIR}/{self.uid}/{download_dict[self.uid].name()}'):
                    share_url += '/'
                    share_url = short_url(share_url)
                    buttons.buildbutton("⚡ 𝗜𝗻𝗱𝗲𝘅 𝗟𝗶𝗻𝗸", share_url)
                else:
                    share_url = short_url(share_url)
                    buttons.buildbutton("⚡ 𝗜𝗻𝗱𝗲𝘅 𝗟𝗶𝗻𝗸", share_url)
                    if VIEW_LINK:
                        share_urls = f'{INDEX_URL}/{url_path}?a=view'
                        share_urls = short_url(share_urls)
                        buttons.buildbutton("🌐 𝗩𝗶𝗲𝘄 𝗟𝗶𝗻𝗸", share_urls)
            if BUTTON_FOUR_NAME is not None and BUTTON_FOUR_URL is not None:
                buttons.buildbutton(f"{BUTTON_FOUR_NAME}", f"{BUTTON_FOUR_URL}")
            if BUTTON_FIVE_NAME is not None and BUTTON_FIVE_URL is not None:
                buttons.buildbutton(f"{BUTTON_FIVE_NAME}", f"{BUTTON_FIVE_URL}")
            if BUTTON_SIX_NAME is not None and BUTTON_SIX_URL is not None:
                buttons.buildbutton(f"{BUTTON_SIX_NAME}", f"{BUTTON_SIX_URL}")
            if self.message.from_user.username:
                uname = f"@{self.message.from_user.username}"
            else:
                uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
            if uname is not None:
                msg += f'\n\n𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗕𝗬: {uname}'
                msg_g = f'\n\n - 𝙽𝚎𝚟𝚎𝚛 𝚂𝚑𝚊𝚛𝚎 𝙸𝚗𝚍𝚎𝚡 𝙻𝚒𝚗𝚔'
                fwdpm = f'\n\n<b>ʏᴏᴜ ᴄᴀɴ ꜰɪɴᴅ ᴜᴘʟᴏᴀᴅ ɪɴ ʙᴏᴛ ᴘᴍ ᴏʀ ᴄʟɪᴄᴋ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ꜱᴇᴇ ᴀᴛ ʟᴏɢ ᴄʜᴀɴɴᴇʟ</b>'
        logmsg = sendLog(msg + msg_g, self.bot, self.update, InlineKeyboardMarkup(buttons.build_menu(2)))
        if logmsg:
            log_m = f"\n\n𝗟𝗶𝗻𝗸 𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗱, 𝗖𝗹𝗶𝗰𝗸 𝗕𝗲𝗹𝗼𝘄 𝗕𝘂𝘁𝘁𝗼𝗻👇"
        else:
            pass
        sendMarkup(msg + fwdpm, self.bot, self.update, InlineKeyboardMarkup([[InlineKeyboardButton(text="𝐂𝐋𝐈𝐂𝐊 𝐇𝐄𝐑𝐄", url=logmsg.link)]]))
        sendPrivate(msg + msg_g, self.bot, self.update, InlineKeyboardMarkup(buttons.build_menu(2)))
        if self.isQbit and QB_SEED:
           return
        else:
            with download_dict_lock:
                try:
                    clean_download(download_dict[self.uid].path())
                except FileNotFoundError:
                    pass
                del download_dict[self.uid]
                count = len(download_dict)
            if count == 0:
                self.clean()
            else:
                update_all_messages()

    def onUploadError(self, error):
        e_str = error.replace('<', '').replace('>', '')
        with download_dict_lock:
            try:
                clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.message.message_id]
            count = len(download_dict)
        sendMessage(f"{self.tag} {e_str}", self.bot, self.update)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

def _mirror(bot, update, isZip=False, extract=False, isQbit=False, isLeech=False, pswd=None):
    if BOT_PM:
      try:
        msg1 = f'Added your Requested Link to Downloads'
        send = bot.sendMessage(update.message.from_user.id, text=msg1, )
        send.delete()
      except Exception as e:
        LOGGER.warning(e)
        bot_d = bot.get_me()
        b_uname = bot_d.username
        uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        buttons = ButtonMaker()
        buttons.buildbutton("Start Me", f"http://t.me/{b_uname}")
        buttons.buildbutton("Updates Channel", "http://t.me/BaashaXclouD")
        reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
        message = sendMarkup(f"Hey Bro {uname}👋,\n\n<b>I Found That You Haven't Started Me In PM Yet 😶</b>\n\nFrom Now on i Will links in PM Only 😇", bot, update, reply_markup=reply_markup)     
        return
    try:
        user = bot.get_chat_member("-1001762089232", update.message.from_user.id)
        LOGGER.error(user.status)
        if user.status not in ('member','creator','administrator'):
            buttons = ButtonMaker()
            buttons.buildbutton("Join Updates Channel", "https://t.me/BaashaXclouD")
            reply_markup = InlineKeyboardMarkup(buttons.build_menu(1))
            sendMarkup(f"<b>⚠️You Have Not Joined My Updates Channel</b>\n\n<b>Join Immediately to use the Bot.</b>", bot, update, reply_markup)
            return
    except:
        pass
    mesg = update.message.text.split('\n')
    message_args = mesg[0].split(' ', maxsplit=1)
    name_args = mesg[0].split('|', maxsplit=1)
    qbitsel = False
    bot_d = bot.get_me()
    b_uname = bot_d.username
    uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
    uid= f"<a>{update.message.from_user.id}</a>"
    try:
        link = message_args[1]
        if link.startswith("s ") or link == "s":
            qbitsel = True
            message_args = mesg[0].split(' ', maxsplit=2)
            link = message_args[2].strip()
        if link.startswith("|") or link.startswith("pswd: "):
            link = ''
    except IndexError:
        link = ''
    try:
        name = name_args[1]
        name = name.split(' pswd: ')[0]
        name = name.strip()
    except IndexError:
        name = ''
    link = resplit(r"pswd:| \|", link)[0]
    link = link.strip()
    pswdMsg = mesg[0].split(' pswd: ')
    if len(pswdMsg) > 1:
        pswd = pswdMsg[1]

    if update.message.from_user.username:
        tag = f"@{update.message.from_user.username}"
    else:
        tag = update.message.from_user.mention_html(update.message.from_user.first_name)

    reply_to = update.message.reply_to_message
    if reply_to is not None:
        file = None
        media_array = [reply_to.document, reply_to.video, reply_to.audio]
        for i in media_array:
            if i is not None:
                file = i
                break
        if (
            not is_url(link)
            and not is_magnet(link)
            or len(link) == 0
        ):
            if not reply_to.from_user.is_bot:
                if reply_to.from_user.username:
                    tag = f"@{reply_to.from_user.username}"
                else:
                    tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)

            if file is None:
                reply_text = reply_to.text
                if is_url(reply_text) or is_magnet(reply_text):
                    link = reply_text.strip()
            elif isQbit:
                file_name = str(time()).replace(".", "") + ".torrent"
                link = file.get_file().download(custom_path=file_name)
            elif file.mime_type != "application/x-bittorrent":
                listener = MirrorListener(bot, update, isZip, extract, isQbit, isLeech, pswd, tag)
                tg_downloader = TelegramDownloadHelper(listener)
                ms = update.message
                tg_downloader.add_download(ms, f'{DOWNLOAD_DIR}{listener.uid}/', name)
                return
            else:
                link = file.get_file().file_path

    if len(mesg) > 1:
        try:
            ussr = quote(mesg[1], safe='')
            pssw = quote(mesg[2], safe='')
            link = link.split("://", maxsplit=1)
            link = f'{link[0]}://{ussr}:{pssw}@{link[1]}'
        except IndexError:
            pass

    if not is_url(link) and not is_magnet(link) and not ospath.exists(link):
        help_msg = "<b>Send link along with command line:</b>"
        help_msg += "\n<code>/command</code> {link} |newname pswd: mypassword [𝚣𝚒𝚙/𝚞𝚗𝚣𝚒𝚙]"
        help_msg += "\n\n<b>By replying to link or file:</b>"
        help_msg += "\n<code>/command</code> |newname pswd: mypassword [𝚣𝚒𝚙/𝚞𝚗𝚣𝚒𝚙]"
        help_msg += "\n\n<b>Direct link authorization:</b>"
        help_msg += "\n<code>/command</code> {link} |newname pswd: mypassword\nusername\npassword"
        help_msg += "\n\n<b>Qbittorrent selection:</b>"
        help_msg += "\n<code>/qbcommand</code> <b>s</b> {link} or by replying to {file}"
        return sendMessage(help_msg, bot, update)

    LOGGER.info(link)
    gdtot_link = is_gdtot_link(link)

    if not is_mega_link(link) and not isQbit and not is_magnet(link) \
       and not ospath.exists(link) and not is_gdrive_link(link) and not link.endswith('.torrent'):
        content_type = get_content_type(link)
        if content_type is None or match(r'text/html|text/plain', content_type):
            try:
                link = direct_link_generator(link)
                LOGGER.info(f"Generated link: {link}")
            except DirectDownloadLinkException as e:
                LOGGER.info(str(e))
                if str(e).startswith('ERROR:'):
                    return sendMessage(str(e), bot, update)
    elif isQbit and not is_magnet(link) and not ospath.exists(link):
        if link.endswith('.torrent'):
            content_type = None
        else:
            content_type = get_content_type(link)
        if content_type is None or match(r'application/x-bittorrent|application/octet-stream', content_type):
            try:
                resp = requests.get(link, timeout=10)
                if resp.status_code == 200:
                    file_name = str(time()).replace(".", "") + ".torrent"
                    open(file_name, "wb").write(resp.content)
                    link = f"{file_name}"
                else:
                    return sendMessage(f"ERROR: link got HTTP response: {resp.status_code}", bot, update)
            except Exception as e:
                error = str(e).replace('<', ' ').replace('>', ' ')
                if error.startswith('No connection adapters were found for'):
                    link = error.split("'")[1]
                else:
                    LOGGER.error(str(e))
                    return sendMessage(error, bot, update)
        else:
            msg = "Qb commands for torrents only. if you are trying to dowload torrent then report."
            return sendMessage(msg, bot, update)

    listener = MirrorListener(bot, update, isZip, extract, isQbit, isLeech, pswd, tag)

    if is_gdrive_link(link):
        if not isZip and not extract and not isLeech:
            gmsg = f"Use /{BotCommands.CloneCommand} to clone Google Drive file/folder\n\n"
            gmsg += f"Use /{BotCommands.ZipMirrorCommand} to make zip of Google Drive folder\n\n"
            gmsg += f"Use /{BotCommands.UnzipMirrorCommand} to extracts Google Drive archive file"
            return sendMessage(gmsg, bot, update)
        Thread(target=add_gd_download, args=(link, listener, gdtot_link)).start()

    elif is_mega_link(link):
        if BLOCK_MEGA_LINKS:
            sendMessage("Mega links are blocked!", bot, update)
            return
        link_type = get_mega_link_type(link)
        if link_type == "folder" and BLOCK_MEGA_FOLDER:
            sendMessage("Mega folder are blocked!", bot, update)
        else:
            sendtextlog(f"<b>User: {uname}</b>\n<b>User ID:</b> <code>/warn {uid}</code>\n\n<b>Link Sended:</b>\n<code>{link}</code>\n\n#MEGA", bot, update)
            Thread(target=add_mega_download, args=(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)).start()

    elif isQbit and (is_magnet(link) or ospath.exists(link)):
        sendtextlog(f"<b>User: {uname}</b>\n<b>User ID:</b> <code>/warn {uid}</code>\n\n<b>Link Sended:</b>\n<code>{link}</code>\n\n#qb", bot, update)
        Thread(target=add_qb_torrent, args=(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener, qbitsel)).start()

    else:
        bot_start = f"http://t.me/{b_uname}?start=start"
        sendtextlog(f"<b>User: {uname}</b>\n<b>User ID:</b> <code>/warn {uid}</code>\n\n<b>Link Sended:</b>\n<code>{link}</code>\n\n#Aria2", bot, update)
        mssg = sendMessage("<b>Processing Your URI...</b>", bot, update)
        sleep(2)
        add_aria2c_download(link, f'{DOWNLOAD_DIR}/{listener.uid}/', listener, name)
        if reply_to is not None:
            editMessage(f"{uname} has sent - \n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n<b>Filename:</b> <code>{file.file_name}</code>\n\n<b>Type:</b> <code>{file.mime_type}</code>\n<b>Size:</b> {get_readable_file_size(file.file_size)}\n\nUser ID : {uid}\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", mssg)
            sleep(1)         
        else:
            editMessage(f"{uname} has sent - \n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n<code>{link}</code>\n\nUser ID : {uid}\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", mssg)
            sleep(1)
        if reply_to is not None:
            sendMessage(f"<b>Hei {uname}</b>\n\n<b>Your Requested Torrent File Has Been Added To The Status</b>\n\n<b>Use /{BotCommands.StatusCommand} To Check Your Progress</b>\n", bot, update)
        elif link.startswith("magnet"):
            sendMessage(f"<b>Hei {uname}</b>\n\n<b>Your Requested Magnet Link Has Been Added To The Status</b>\n\n<b>Use /{BotCommands.StatusCommand} To Check Your Progress</b>\n", bot, update)
        elif link.endswith(".torrent"):
            sendMessage(f"<b>Hei {uname}</b>\n\n<b>Your Requested Torrent Link Has Been Added To The Status</b>\n\n<b>Use /{BotCommands.StatusCommand} To Check Your Progress</b>\n", bot, update)
        elif '0:/' in link or '1:/' in link or '2:/' in link or '3:/' in link or '4:/' in link or '5:/' in link or '6:/' in link or "workers.dev" in link:
            sendMessage(f"<b>Hei {uname}</b>\n\n<b>Your Requested Index Link Has Been Added To The Status</b>\n\n<b>Use /{BotCommands.StatusCommand} To Check Your Progress</b>\n", bot, update)
        else:
            sendMessage(f"<b>Hei {uname}</b>\n\n<b>Your Requested DDL Has Been Added To The Status</b>\n\n<b>Use /{BotCommands.StatusCommand} To Check Your Progress</b>\n", bot, update)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))

def mirror(update, context):
    _mirror(context.bot, update)

def unzip_mirror(update, context):
    _mirror(context.bot, update, extract=True)

def zip_mirror(update, context):
    _mirror(context.bot, update, True)

def qb_mirror(update, context):
    _mirror(context.bot, update, isQbit=True)

def qb_unzip_mirror(update, context):
    _mirror(context.bot, update, extract=True, isQbit=True)

def qb_zip_mirror(update, context):
    _mirror(context.bot, update, True, isQbit=True)

def leech(update, context):
    _mirror(context.bot, update, isLeech=True)

def unzip_leech(update, context):
    _mirror(context.bot, update, extract=True, isLeech=True)

def zip_leech(update, context):
    _mirror(context.bot, update, True, isLeech=True)

def qb_leech(update, context):
    _mirror(context.bot, update, isQbit=True, isLeech=True)

def qb_unzip_leech(update, context):
    _mirror(context.bot, update, extract=True, isQbit=True, isLeech=True)

def qb_zip_leech(update, context):
    _mirror(context.bot, update, True, isQbit=True, isLeech=True)

mirror_handler = CommandHandler(BotCommands.MirrorCommand, mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
unzip_mirror_handler = CommandHandler(BotCommands.UnzipMirrorCommand, unzip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
zip_mirror_handler = CommandHandler(BotCommands.ZipMirrorCommand, zip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_mirror_handler = CommandHandler(BotCommands.QbMirrorCommand, qb_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_unzip_mirror_handler = CommandHandler(BotCommands.QbUnzipMirrorCommand, qb_unzip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_zip_mirror_handler = CommandHandler(BotCommands.QbZipMirrorCommand, qb_zip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
leech_handler = CommandHandler(BotCommands.LeechCommand, leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
unzip_leech_handler = CommandHandler(BotCommands.UnzipLeechCommand, unzip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
zip_leech_handler = CommandHandler(BotCommands.ZipLeechCommand, zip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_leech_handler = CommandHandler(BotCommands.QbLeechCommand, qb_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_unzip_leech_handler = CommandHandler(BotCommands.QbUnzipLeechCommand, qb_unzip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_zip_leech_handler = CommandHandler(BotCommands.QbZipLeechCommand, qb_zip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)

dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(unzip_mirror_handler)
dispatcher.add_handler(zip_mirror_handler)
dispatcher.add_handler(qb_mirror_handler)
dispatcher.add_handler(qb_unzip_mirror_handler)
dispatcher.add_handler(qb_zip_mirror_handler)
dispatcher.add_handler(leech_handler)
dispatcher.add_handler(unzip_leech_handler)
dispatcher.add_handler(zip_leech_handler)
dispatcher.add_handler(qb_leech_handler)
dispatcher.add_handler(qb_unzip_leech_handler)
dispatcher.add_handler(qb_zip_leech_handler)
