# corrected time-string parser, identical semantics to build_canonical.seg_blocks
import pools_past as PP
DAY = PP.DAY
def parse_fixed(t):
    tm = 0
    for seg in str(t or '').split('/'):
        day, num = None, ''
        for ch in seg + '#':
            if ch.isdigit():
                num += ch; continue
            if num:
                if day is not None and 1 <= int(num) <= 15:
                    tm |= 1 << (day * 16 + int(num))
                num = ''
            if ch in DAY:
                day = DAY[ch]
    return tm
