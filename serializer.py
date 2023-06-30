
import struct


def iota(cls):
    idx = 0
    for attr in cls.__dict__:
        if attr.startswith('_'):
            continue
        setattr(cls, attr, idx)
        idx += 1
    return cls


@iota
class Type:
    NONE = 0
    RAW = 0
    STR = 0
    BOOL = 0
    INT = 0
    LONG = 0

    FLOAT = 0
    TUPLE = 0
    LIST = 0
    DICT = 0
    TAGGED_DICT = 0


MAX_INT_POSITIVE = 2 ** 31 - 1
MAX_INT_NEGATIVE = -2 ** 31


class SerializeError(Exception):
    pass


def serialize(v):
    """a simple python tag-length-value(TLV) serializer
    """
    if v is None:
        return _varint_encode(Type.NONE)
    if isinstance(v, bytes):
        return _varint_encode(Type.RAW) + _varint_encode(len(v)) + v
    if isinstance(v, str):
        b = v.encode('utf-8')
        return _varint_encode(Type.STR) + _varint_encode(len(b)) + b
    if isinstance(v, bool):
        return _varint_encode(Type.BOOL) + (b'\x01' if v else b'\x00')
    if isinstance(v, int):
        if v > MAX_INT_POSITIVE or v < MAX_INT_NEGATIVE:
            return _varint_encode(Type.LONG) + struct.pack('>q', v)
        else:
            return _varint_encode(Type.INT) + struct.pack('>i', v)
    if isinstance(v, float):
        return _varint_encode(Type.FLOAT) + struct.pack('>f', v)
    if isinstance(v, tuple):
        b = b''
        for vv in v:
            b += serialize(vv)
        return _varint_encode(Type.TUPLE) + _varint_encode(len(b)) + b
    if isinstance(v, list):
        b = b''
        for vv in v:
            b += serialize(vv)
        return _varint_encode(Type.LIST) + _varint_encode(len(b)) + b
    if isinstance(v, dict):
        b = b''
        for k, vv in v.items():
            b += serialize(k)
            b += serialize(vv)
        return _varint_encode(Type.DICT) + _varint_encode(len(b)) + b
    # todo: tagged dict
    
    raise SerializeError("unsupported type")


def deserialize(vb):
    """a simple python tag-length-value(TLV) deserializer
    """
    t, cnt = _varint_decode(vb)
    if t == Type.NONE:
        return None, cnt
    if t == Type.RAW:
        l, c = _varint_decode(vb[cnt:])
        cnt += c
        return vb[cnt:cnt + l], cnt + l
    if t == Type.STR:
        l, c = _varint_decode(vb[cnt:])
        cnt += c
        return vb[cnt:cnt + l].decode('utf-8'), cnt + l
    if t == Type.BOOL:
        b = vb[cnt:cnt + 1]
        cnt += 1
        return b == b'\x01', cnt
    if t == Type.INT:
        return struct.unpack('>i', vb[cnt:cnt + 4])[0], cnt + 4
    if t == Type.LONG:
        return struct.unpack('>q', vb[cnt:cnt + 8])[0], cnt + 8
    if t == Type.FLOAT:
        return struct.unpack('>f', vb[cnt:cnt + 4])[0], cnt + 4
    if t == Type.TUPLE:
        l, c = _varint_decode(vb[cnt:])
        cnt += c
        if l == 0:
            return (), cnt
        lst = []
        while True:
            v, c = deserialize(vb[cnt:])
            lst.append(v)
            cnt += c
            l -= c
            if l == 0:
                break
            if l < 0:
                raise SerializeError("invalid tuple")
        return tuple(lst), cnt
    if t == Type.LIST:
        l, c = _varint_decode(vb[cnt:])
        cnt += c
        if l == 0:
            return [], cnt
        lst = []
        while True:
            v, c = deserialize(vb[cnt:])
            lst.append(v)
            cnt += c
            l -= c
            if l == 0:
                break
            if l < 0:
                raise SerializeError("invalid list")
        return lst, cnt
    if t == Type.DICT:
        l, c = _varint_decode(vb[cnt:])
        cnt += c
        if l == 0:
            return {}, cnt
        dct = {}
        while True:
            k, c = deserialize(vb[cnt:])
            cnt += c
            l -= c
            v, c = deserialize(vb[cnt:])
            cnt += c
            l -= c
            dct[k] = v
            if l == 0:
                break
            if l < 0:
                raise SerializeError("invalid dict")
        return dct, cnt
    
    raise SerializeError("unsupported type")


def _varint_encode(v):
    """simple varint encode implementation

    Args:
        v (int): 
    """
    if v < 0:
        raise SerializeError("negetive varint")
    c = False  # continuation bit
    r = b''  # result
    while True:
        vq = v & 0x7F
        if c:
            vq |= 0x80
        b = vq.to_bytes(1, byteorder='big')
        r = b + r

        v >>= 7
        if v == 0:
            break
        c = True
    return r
    


def _varint_decode(vb):
    """simple varint decode implementation

    Args:
        vb (bytes): 
    """
    r = 0  # result
    c = False  # continuation bit
    cnt = 0  # count of bytes
    for v in vb:
        r = (r << 7) | (v & 0x7F)
        cnt += 1
        if (v & 0x80) == 0:
            c = False
            break
        c = True
    if c:
        raise SerializeError("invalid varint")
    return r, cnt

