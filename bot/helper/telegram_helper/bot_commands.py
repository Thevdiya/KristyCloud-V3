import os
from bot import BOT_NO

def getCommand(name: str, command: str):
    try:
        if len(os.environ[name]) == 0:
            raise KeyError
        return os.environ[name]
    except KeyError:
        return command

class _BotCommands:
    def __init__(self):
        self.StartCommand = getCommand('START_BOT', 'start')
        self.MirrorCommand = getCommand('MIRROR_BOT', f'mir{BOT_NO}')
        self.UnzipMirrorCommand = getCommand('UNZIP_BOT', f'mirunzip{BOT_NO}')
        self.ZipMirrorCommand = getCommand('ZIP_BOT', f'mirzip{BOT_NO}')
        self.CancelMirror = getCommand('CANCEL_BOT', f'cancel{BOT_NO}')
        self.CancelAllCommand = getCommand('CANCEL_ALL_BOT', 'cancelall')
        self.ListCommand = getCommand('LIST_BOT', f'list{BOT_NO}')
        self.SearchCommand = getCommand('SEARCH_BOT', f'search{BOT_NO}')
        self.StatusCommand = getCommand('STATUS_BOT', f'status{BOT_NO}')
        self.AuthorizedUsersCommand = getCommand('USERS_BOT', f'users{BOT_NO}')
        self.AuthorizeCommand = getCommand('AUTH_BOT', f'auth{BOT_NO}')
        self.UnAuthorizeCommand = getCommand('UNAUTH_BOT', f'unauth{BOT_NO}')
        self.AddSudoCommand = getCommand('ADDSUDO_BOT', f'addsudo{BOT_NO}')
        self.RmSudoCommand = getCommand('RMSUDO_BOT', f'rmsudo{BOT_NO}')
        self.PingCommand = getCommand('PING_BOT', 'ping')
        self.RestartCommand = getCommand('RESTART_BOT', f'rs{BOT_NO}')
        self.StatsCommand = getCommand('STATS_BOT', f'stats{BOT_NO}')
        self.HelpCommand = getCommand('HELP_BOT', f'help{BOT_NO}')
        self.LogCommand = getCommand('LOG_BOT', f'logs{BOT_NO}')
        self.SpeedCommand = getCommand('SPEED_BOT', 'speedtest')
        self.CloneCommand = getCommand('CLONE_BOT', f'clone{BOT_NO}')
        self.GDToTCommand = getCommand('GDTOT_BOT', f'gdtot{BOT_NO}')
        self.CountCommand = getCommand('COUNT_BOT', f'count{BOT_NO}')
        self.WatchCommand = getCommand('YTDL_BOT', f'yt{BOT_NO}')
        self.ZipWatchCommand = getCommand('ZIPWATCH_BOT', f'zipwatch{BOT_NO}')
        self.QbMirrorCommand = getCommand('QBITMIR_BOT', f'mirqb{BOT_NO}')
        self.QbUnzipMirrorCommand = getCommand('QBITUNZIP_BOT', f'unzipqb{BOT_NO}')
        self.QbZipMirrorCommand = getCommand('QBITZIP_BOT', f'zipqb{BOT_NO}')
        self.DeleteCommand = getCommand('DELETE_BOT', f'del{BOT_NO}')
        self.ShellCommand = getCommand('SHELL_BOT', f'shell{BOT_NO}')
        self.ExecHelpCommand = getCommand('EXEHELP_BOT', f'exehelp{BOT_NO}')
        self.LeechSetCommand = getCommand('LEECH_SET', f'leechset{BOT_NO}')
        self.SetThumbCommand = getCommand('SET_THUMB', f'setthumb{BOT_NO}')
        self.LeechCommand = getCommand('LEECH_BOT', f'leech{BOT_NO}')
        self.UnzipLeechCommand = getCommand('UNZIP_LEECH', f'leechunzip{BOT_NO}')
        self.ZipLeechCommand = getCommand('ZIP_LEECH', f'zipleech{BOT_NO}')
        self.QbLeechCommand = getCommand('QBIT_LEECH', f'qbleech{BOT_NO}')
        self.QbUnzipLeechCommand = getCommand('QBITUNZIP_LEECH',  f'qbunzipleech{BOT_NO}')
        self.QbZipLeechCommand = getCommand('QBITZIP_LEECH', f'qbzipleech{BOT_NO}')
        self.LeechWatchCommand = getCommand('WATCH_LEECH', f'ytleech{BOT_NO}')
        self.LeechZipWatchCommand = getCommand('WATCHZIP_LEECH', f'leechzipwatch{BOT_NO}')
        self.RssListCommand = getCommand('RSS_LIST', f'rsslist{BOT_NO}')
        self.RssGetCommand = getCommand('RSS_GET', f'rssget{BOT_NO}')
        self.RssSubCommand = getCommand('RSS_SUB', f'rsssub{BOT_NO}')
        self.RssUnSubCommand = getCommand('RSS_UNSUB', f'rssunsub{BOT_NO}')
        self.RssUnSubAllCommand = getCommand('RSS_UNSUBALL', f'rssunsuball{BOT_NO}')
        self.UsageCommand = getCommand('USAGE_BOT', f'usage{BOT_NO}')

BotCommands = _BotCommands()
