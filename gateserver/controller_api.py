from .controller_protocol import *
from . import db
from . import utils

def get_key_for_mac(mac):
    """Loads the key for this controller from the DB."""
    rs = db.exec_sql('SELECT key FROM controller WHERE id = %s',
                     (utils.bytes2mac(mac),), ret=True)
    checkmsg(len(rs) == 1, 'unknown controllerID ')
    return rs[0]['key'].tobytes()

def fstring(buf):
    """See https://github.com/fmfi-svt-gate/server/wiki/Controller-%E2%86%94-Server-Protocol#note-isic-ids-representation"""
    length, string = int(buf[0]), buf[1:]
    checkmsg(length <= len(string), 'fstring length > buffer size')
    return string[:length]

process_request = {
    MsgType.OPEN:
        lambda data: ((S.OK if fstring(data) == b'Hello' else S.ERR), None),
}
assert set(MsgType) == set(process_request), 'Not all message types are handled'

def log_message(controllerID, req_type, indata, status):
    """TODO"""
    print(utils.bytes2mac(controllerID), req_type.name, indata, '->', status.name)

def log_bad_packet(buf, e):
    """TODO"""
    raise e

def handle_request(buf):
    try:
        packet_head, payload = parse_packet_head(buf)
        key = get_key_for_mac(packet_head.controllerID)
        req_head, req_type, indata = parse_r(RequestHead, packet_head, key, payload)
        status, outdata = process_request[req_type](indata)
        log_message(packet_head.controllerID, req_type, indata, status)
        return make_reply_for(packet_head, req_head, key, status, outdata)
    except BadMessageError as e:
        log_bad_packet(buf, e)
