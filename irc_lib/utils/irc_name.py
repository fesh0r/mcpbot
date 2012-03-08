import socket


def get_nick(name):
    if name[0] == ':':
        print '*** irc_name.get_nick: : in nick: %s' % repr(name)
        name = name[1:]
    nick, _, _ = split_prefix(name)
    return nick


def get_host(name):
    _, _, host = split_prefix(name)
    return host


def get_ip(host):
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        print '*** irc_name.get_ip: socket.gaierror: %s' % repr(host)
        return '0.0.0.0'


def split_prefix(prefix):
    rest, _, host = prefix.partition('@')
    nick, _, user = rest.partition('!')
    return nick, user, host
