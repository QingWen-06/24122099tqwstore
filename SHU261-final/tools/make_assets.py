#!/usr/bin/env python3
"""声音资产剪辑/导出管线（纯标准库，无第三方依赖）。

职责：读入任意 PCM WAV（8/16/24/32 bit、单/多声道），做去直流、高通、
      归一化、淡入淡出、削减静音、多段拼接、无缝循环化、重采样，
      并统一导出为 **48 kHz / 24 bit / stereo** WAV。

子命令：
    stats   <file> ...                     只看统计，不改文件
    spot    --in <file> --out <file> [...]  剪辑"随机间断声"（单条）
    base    --in <a.wav> <b.wav> ... --out <file> [...]  拼接"基底持续声"并做无缝循环

通用参数：
    --hp <Hz>        高通频率（去低频嗡鸣/直流），默认 40
    --lp <Hz>        低通频率，默认 0（不启用）
    --sr <Hz>        导出采样率，默认 48000
    --peak <dBFS>    峰值上限（真峰值限制只做线性缩放），默认 -3
    --gain <dB>      额外增益，默认 0

spot 专用：
    --rms <dBFS>        目标 RMS（0 表示不启用），默认 -20
    --trim-silence <dB> 静音阈值，头部尾部低于此值切除，默认 -55
    --pad <s>           前后各留静音，默认 0.02
    --fade-in <s>       默认 0.003
    --fade-out <s>      默认 0.05

base 专用：
    --target-len <s>    目标成品长度，默认 0（= 输入拼接后全长）
    --xfade <s>         段间/循环接缝交叉淡化长度，默认 1.0
    --keep-stereo       保留原立体声；默认对单声道做伪立体声展开
"""
import os
import sys
import wave
import array
import math
import argparse

SR_OUT = 48000
SIGN_TABLE = bytes(0xFF if s & 0x80 else 0x00 for s in range(256))


# ---------------------------------------------------------------- WAV 读写
def read_pcm(path):
    """读 PCM WAV，返回 (nch, sr, [array('d') 每声道, 幅度已归一到 -1..1])。"""
    with wave.open(path, "rb") as w:
        nch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if nch < 1:
        raise SystemExit("声道数异常")
    if sw == 1:  # 8bit 无符号
        scale = 128.0
        ints = array.array("b", bytes((b - 128) & 0xFF for b in raw))
    elif sw == 2:
        scale = 32768.0
        ints = array.array("h")
        ints.frombytes(raw[: (len(raw) // 2) * 2])
    elif sw == 3:
        # 关键：用 C 级切片把 24bit 扩展成 int32（补符号位），保留全部 24bit 精度
        m = len(raw) // 3
        buf = bytearray(4 * m)
        buf[0::4] = raw[0: 3 * m: 3]
        buf[1::4] = raw[1: 3 * m: 3]
        buf[2::4] = raw[2: 3 * m: 3]
        buf[3::4] = raw[2: 3 * m: 3].translate(SIGN_TABLE)
        scale = 8388608.0
        ints = array.array("i")
        ints.frombytes(bytes(buf))
    elif sw == 4:
        scale = 2147483648.0
        ints = array.array("i")
        ints.frombytes(raw[: (len(raw) // 4) * 4])
    else:
        raise SystemExit(f"不支持的位深 {sw * 8} bit")

    frames = len(ints) // nch
    chans = [array.array("d", [0.0]) * 0 for _ in range(nch)]
    chans = [array.array("d", bytes(8 * frames)) for _ in range(nch)]
    if nch == 1:
        chans[0] = array.array("d", (v / scale for v in ints))
    else:
        for c in range(nch):
            chans[c] = array.array("d", (ints[i] / scale for i in range(c, frames * nch, nch)))
    return nch, sr, chans


def write_pcm24(path, sr, chans):
    """写 48k/24bit WAV（stereo 或多声道）。chans 为 array('d')，幅度 -1..1。"""
    nch = len(chans)
    n = len(chans[0])
    ints = array.array("i", bytes(4 * n * nch))
    lim = 8388607
    for c in range(nch):
        src = chans[c]
        base = c
        for i in range(n):
            v = int(round(src[i] * 8388608.0))
            if v > lim:
                v = lim
            elif v < -lim:
                v = -lim
            ints[i * nch + base] = v
    buf = bytearray(ints.tobytes())
    del buf[3::4]  # 去掉每个 int32 的最高字节 → 3 字节 24bit
    with wave.open(path, "wb") as w:
        w.setnchannels(nch)
        w.setsampwidth(3)
        w.setframerate(sr)
        w.writeframes(bytes(buf))


# ---------------------------------------------------------------- 基础测量
def db(x):
    return 20.0 * math.log10(x) if x > 0 else -999.0


def peak_of(chans):
    p = 0.0
    for x in chans:
        for v in x:
            av = v if v >= 0 else -v
            if av > p:
                p = av
    return p


def rms_of(chans):
    tot = 0.0
    cnt = 0
    for x in chans:
        s = 0.0
        for v in x:
            s += v * v
        tot += s
        cnt += len(x)
    return math.sqrt(tot / cnt) if cnt else 0.0


def dc_of(chans):
    return sum(sum(x) / len(x) for x in chans) / len(chans)


# ---------------------------------------------------------------- 处理
def remove_dc(chans):
    for c in range(len(chans)):
        m = sum(chans[c]) / len(chans[c])
        chans[c] = array.array("d", (v - m for v in chans[c]))


def biquad(chans, sr, fc, q=0.70710678, kind="hp"):
    """二阶 Butterworth 高通/低通（RBJ cookbook）。"""
    w0 = 2.0 * math.pi * fc / sr
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    if kind == "hp":
        b0 = (1 + cw) / 2
        b1 = -(1 + cw)
        b2 = (1 + cw) / 2
    else:
        b0 = (1 - cw) / 2
        b1 = 1 - cw
        b2 = (1 - cw) / 2
    a0 = 1 + alpha
    a1 = -2 * cw
    a2 = 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    for c in range(len(chans)):
        x = chans[c]
        y = array.array("d", bytes(8 * len(x)))
        x1 = x2 = y1 = y2 = 0.0
        for i in range(len(x)):
            xi = x[i]
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2 = x1
            x1 = xi
            y2 = y1
            y1 = yi
            y[i] = yi
        chans[c] = y


def resample(chans, sr_in, sr_out):
    if sr_in == sr_out:
        return chans
    ratio = sr_out / float(sr_in)
    for c in range(len(chans)):
        x = chans[c]
        n_out = int(len(x) * ratio)
        y = array.array("d", bytes(8 * n_out))
        for i in range(n_out):
            pos = i / ratio
            i0 = int(pos)
            i1 = i0 + 1 if i0 + 1 < len(x) else i0
            frac = pos - i0
            y[i] = x[i0] * (1.0 - frac) + x[i1] * frac
        chans[c] = y
    return chans


def to_stereo(chans, pseudo=True):
    if len(chans) >= 2:
        return [chans[0], chans[1]]
    if not pseudo:
        return [chans[0], array.array("d", chans[0])]
    # 伪立体声：右声道做 12ms 微延迟 + 反向轻微高通，制造空间差异
    x = chans[0]
    d = int(0.012 * SR_OUT)
    r = array.array("d", bytes(8 * len(x)))
    for i in range(len(x)):
        r[i] = x[i - d] if i >= d else 0.0
    return [x, r]


def scale(chans, g):
    if g == 1.0:
        return
    for c in range(len(chans)):
        chans[c] = array.array("d", (v * g for v in chans[c]))


def apply_gain(chans, target_rms_db=0.0, ceiling_db=-3.0, extra_db=0.0):
    """按 RMS 归一化，并用峰值天花板限制（只做线性缩放，不压限）。"""
    info = {}
    if target_rms_db:
        cur = rms_of(chans)
        need = target_rms_db - db(cur)
        g = 10.0 ** (need / 20.0)
        p = peak_of(chans) * g
        if p > 10 ** (ceiling_db / 20.0):
            g = (10 ** (ceiling_db / 20.0)) / peak_of(chans)
            info["ceiling_hit"] = True
        scale(chans, g)
        info["gain_db"] = db(g)
    if extra_db:
        scale(chans, 10.0 ** (extra_db / 20.0))
    p = peak_of(chans)
    if p > 10 ** (ceiling_db / 20.0):
        g = (10 ** (ceiling_db / 20.0)) / p
        scale(chans, g)
        info["final_trim_db"] = db(g)
    info["peak_db"] = db(peak_of(chans))
    info["rms_db"] = db(rms_of(chans))
    return info


def flatten_level(chans, sr, win_s=0.25, smooth_s=2.0, max_db=8.0):
    """把整段录音的响度漂移压平（手机录音时走动/风扇变速造成的长时电平变化）。

    做法：按 win_s 计算短时 RMS，求中位电平作为目标，算出每窗需要的修正增益(dB)，
    对修正曲线做 smooth_s 秒平滑（避免"抽吸"感），再逐样本线性插值应用。
    修正量被限制在 ±max_db 以内，绝不改变动态内容本身。
    """
    n = len(chans[0])
    win = max(1, int(win_s * sr))
    nch = len(chans)
    centers, levels = [], []
    for s in range(0, max(n - win + 1, 1), win):
        acc = 0.0
        for c in chans:
            acc += sum(v * v for v in c[s: s + win])
        r = math.sqrt(acc / (win * nch))
        centers.append(s + win / 2.0)
        levels.append(db(r))
    if len(levels) < 3:
        return {"flatten_db": 0.0}
    srt = sorted(levels)
    target = srt[len(srt) // 2]
    corr = [max(-max_db, min(max_db, target - g)) for g in levels]
    k = max(1, int(smooth_s / win_s))
    smoothed = []
    for i in range(len(corr)):
        lo, hi = max(0, i - k // 2), min(len(corr), i + k // 2 + 1)
        smoothed.append(sum(corr[lo:hi]) / (hi - lo))
    lo_db, hi_db = min(smoothed), max(smoothed)
    for c in range(nch):
        x = chans[c]
        j = 0
        for i in range(n):
            while j + 1 < len(centers) - 1 and i > centers[j + 1]:
                j += 1
            if j + 1 < len(centers):
                t = (i - centers[j]) / max(centers[j + 1] - centers[j], 1.0)
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                g_db = smoothed[j] * (1 - t) + smoothed[j + 1] * t
            else:
                g_db = smoothed[-1]
            x[i] *= 10.0 ** (g_db / 20.0)
    return {"flatten_db": hi_db - lo_db, "target_db": target}


def fade(chans, sr, fin=0.0, fout=0.0):
    n = len(chans[0])
    ni = int(fin * sr)
    no = int(fout * sr)
    for c in range(len(chans)):
        x = chans[c]
        for i in range(min(ni, n)):
            x[i] *= i / ni
        for i in range(min(no, n)):
            x[n - 1 - i] *= i / no


def trim_silence(chans, sr, thresh_db, pad=0.02):
    """按 10ms 块找首尾有声区，切掉前后静音，并留 pad 秒。"""
    n = len(chans[0])
    blk = max(1, int(sr * 0.01))
    thr = 10 ** (thresh_db / 20.0)
    first, last = 0, n - 1
    c0 = chans[0]
    for s in range(0, n - blk, blk):
        pk = 0.0
        for i in range(s, s + blk):
            av = c0[i] if c0[i] >= 0 else -c0[i]
            if av > pk:
                pk = av
        if pk > thr:
            first = s
            break
    for s in range(n - blk, 0, -blk):
        pk = 0.0
        for i in range(s, min(s + blk, n)):
            av = c0[i] if c0[i] >= 0 else -c0[i]
            if av > pk:
                pk = av
        if pk > thr:
            last = min(s + blk, n) - 1
            break
    p = int(pad * sr)
    first = max(0, first - p)
    last = min(n - 1, last + p)
    return [array.array("d", x[first: last + 1]) for x in chans]


def concat_xfade(segs, sr, xfade_s):
    """多段等功率交叉淡化拼接。"""
    if not segs:
        raise SystemExit("没有可拼接的段")
    k = int(xfade_s * sr)
    out = [array.array("d", segs[0][c]) for c in range(len(segs[0]))]
    for seg in segs[1:]:
        for c in range(len(out)):
            a, b = out[c], seg[c]
            kk = min(k, len(a), len(b))
            if kk <= 1:
                out[c] = array.array("d", list(a) + list(b))
                continue
            tail = a[len(a) - kk:]
            head = b[:kk]
            mixed = array.array("d", bytes(8 * kk))
            for i in range(kk):
                t = i / (kk - 1)
                gi = math.cos(t * math.pi / 2)   # 等功率
                go = math.sin(t * math.pi / 2)
                mixed[i] = tail[i] * gi + head[i] * go
            out[c] = array.array("d", list(a[: len(a) - kk]) + list(mixed) + list(b[kk:]))
    return out


def loopify(chans, sr, xfade_s, target_len_s=0.0):
    """把一段声音做成无缝循环：尾部 xfade 段等功率叠到头部，并裁掉尾部。"""
    n = len(chans[0])
    k = int(xfade_s * sr)
    if target_len_s and int(target_len_s * sr) < n:
        n = int(target_len_s * sr)
        chans = [array.array("d", x[:n]) for x in chans]
    if k <= 1 or k >= n:
        return chans
    out = []
    for x in chans:
        head = array.array("d", x[:n - k])
        tail = x[n - k:]
        for i in range(k):
            t = i / (k - 1)
            gi = math.sin(t * math.pi / 2)   # 循环起点用渐入，尾部渐出
            go = math.cos(t * math.pi / 2)
            head[i] = head[i] * gi + tail[i] * go
        out.append(head)
    return out


# ---------------------------------------------------------------- 统计输出
def describe(path):
    nch, sr, chans = read_pcm(path)
    n = len(chans[0])
    print(f"{os.path.basename(path)}: {nch}ch {sr}Hz {n / sr:.2f}s 24bit源  "
          f"peak {db(peak_of(chans)):.1f} dBFS  rms {db(rms_of(chans)):.1f} dBFS  "
          f"dc {dc_of(chans):+.5f}")
    return nch, sr, chans


# ---------------------------------------------------------------- 子命令
def cmd_stats(a):
    for p in a.input:
        describe(p)


def cmd_spot(a):
    nch, sr, chans = read_pcm(a.inp)
    print(f"[读入] {os.path.basename(a.inp)} {nch}ch {sr}Hz {len(chans[0])/sr:.2f}s "
          f"peak {db(peak_of(chans)):.1f} rms {db(rms_of(chans)):.1f}")
    remove_dc(chans)
    if a.hp:
        biquad(chans, sr, a.hp, kind="hp")
    if a.lp:
        biquad(chans, sr, a.lp, kind="lp")
    if a.trim_silence is not None:
        before = len(chans[0]) / sr
        chans = trim_silence(chans, sr, a.trim_silence, a.pad)
        print(f"[削静音] {before:.2f}s -> {len(chans[0])/sr:.2f}s")
    chans = resample(chans, sr, a.sr)
    chans = to_stereo(chans, pseudo=True)
    fade(chans, a.sr, a.fade_in, a.fade_out)
    info = apply_gain(chans, a.rms, a.peak, a.gain)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    write_pcm24(a.out, a.sr, chans)
    print(f"[导出] {a.out}  48k/24bit/stereo  {len(chans[0])/a.sr:.2f}s")
    print(f"       增益 {info.get('gain_db', 0):+.1f} dB  "
          f"peak {info['peak_db']:.1f} dBFS  rms {info['rms_db']:.1f} dBFS"
          + ("  [撞到峰值天花板，已回退]" if info.get("ceiling_hit") else ""))


def cmd_base(a):
    segs = []
    for p in a.input:
        nch, sr, chans = read_pcm(p)
        print(f"[读入] {os.path.basename(p)} {nch}ch {sr}Hz {len(chans[0])/sr:.2f}s "
              f"peak {db(peak_of(chans)):.1f} rms {db(rms_of(chans)):.1f}")
        remove_dc(chans)
        if a.hp:
            biquad(chans, sr, a.hp, kind="hp")
        if a.lp:
            biquad(chans, sr, a.lp, kind="lp")
        chans = resample(chans, sr, a.sr)
        chans = to_stereo(chans, pseudo=not a.keep_stereo)
        # 各段先做 RMS 对齐，避免某段过响压掉别的层
        apply_gain(chans, a.seg_rms, a.peak, 0.0)
        if a.flatten:
            fl = flatten_level(chans, a.sr)
            print(f"[压平漂移] 修正范围 {fl.get('flatten_db', 0):.1f} dB，"
                  f"目标电平 {fl.get('target_db', 0):.1f} dBFS")
        segs.append(chans)
    print(f"[拼接] {len(segs)} 段，交叉淡化 {a.xfade}s")
    merged = concat_xfade(segs, a.sr, a.xfade)
    print(f"       拼接后 {len(merged[0])/a.sr:.2f}s")
    merged = loopify(merged, a.sr, a.xfade, a.target_len)
    print(f"[循环化] 接缝 {a.xfade}s 等功率淡化 -> {len(merged[0])/a.sr:.2f}s")
    info = apply_gain(merged, a.rms, a.peak, a.gain)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    write_pcm24(a.out, a.sr, merged)
    print(f"[导出] {a.out}  48k/24bit/stereo  {len(merged[0])/a.sr:.2f}s")
    print(f"       增益 {info.get('gain_db', 0):+.1f} dB  "
          f"peak {info['peak_db']:.1f} dBFS  rms {info['rms_db']:.1f} dBFS"
          + ("  [撞到峰值天花板，已回退]" if info.get("ceiling_hit") else ""))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("stats")
    ps.add_argument("input", nargs="+")
    ps.set_defaults(func=cmd_stats)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", required=True)
    common.add_argument("--hp", type=float, default=40.0)
    common.add_argument("--lp", type=float, default=0.0)
    common.add_argument("--sr", type=int, default=SR_OUT)
    common.add_argument("--peak", type=float, default=-3.0)
    common.add_argument("--gain", type=float, default=0.0)

    p1 = sub.add_parser("spot", parents=[common])
    p1.add_argument("--in", dest="inp", required=True)
    p1.add_argument("--rms", type=float, default=-20.0)
    p1.add_argument("--trim-silence", type=float, default=-55.0)
    p1.add_argument("--pad", type=float, default=0.02)
    p1.add_argument("--fade-in", type=float, default=0.003)
    p1.add_argument("--fade-out", type=float, default=0.05)
    p1.set_defaults(func=cmd_spot)

    p2 = sub.add_parser("base", parents=[common])
    p2.add_argument("--in", dest="input", nargs="+", required=True)
    p2.add_argument("--rms", type=float, default=-23.0)
    p2.add_argument("--seg-rms", type=float, default=-26.0)
    p2.add_argument("--xfade", type=float, default=1.0)
    p2.add_argument("--target-len", type=float, default=0.0)
    p2.add_argument("--flatten", action="store_true", help="压平长时响度漂移")
    p2.add_argument("--keep-stereo", action="store_true")
    p2.set_defaults(func=cmd_base)

    a = ap.parse_args(argv[1:])
    a.func(a)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
