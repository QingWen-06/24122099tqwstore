#!/usr/bin/env python3
"""WAV 体检工具（纯标准库，无第三方依赖）。

用途：在正式录音前快速验证手机录音文件是否可用。

用法：
    python inspect_wav.py <文件或目录> [更多文件...]

输出：格式（容器/编码/采样率/位深/声道）、时长、峰值、RMS、直流偏移、
      削波采样数、前 0.5 秒静音底噪电平，并给出 PASS/WARN/FAIL 判定。
"""
import os
import sys
import wave
import struct
import math
import array


def fmt_db(x):
    if x <= 0:
        return "-inf dBFS"
    return f"{20.0 * math.log10(x):+.1f} dBFS"


def inspect(path):
    print("=" * 74)
    print(f"文件：{path}")
    size = os.path.getsize(path)
    print(f"大小：{size / 1048576:.2f} MB")

    try:
        with wave.open(path, "rb") as w:
            ch = w.getnchannels()
            sw = w.getsampwidth()
            sr = w.getframerate()
            n = w.getnframes()
            comp = w.getcomptype()
            raw = w.readframes(n)
    except wave.Error as e:
        print(f"[FAIL] 不是可解析的 PCM WAV：{e}")
        print("       → 若是 .m4a/.mp3/.aac，请换能录 WAV 的 App 重录（见 recording-guide.md）")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] 打不开文件：{e}")
        return False

    dur = n / float(sr) if sr else 0.0
    print(f"容器：WAV / {comp}   编码位深：{sw * 8} bit   采样率：{sr} Hz   声道：{ch}")
    print(f"时长：{dur:.2f} s   样本帧数：{n}")

    # 统一转成 float 列表（-1.0 ~ 1.0）
    if sw == 1:
        vals = [(b - 128) / 128.0 for b in raw]
    elif sw == 2:
        a = array.array("h")
        a.frombytes(raw[: len(raw) // 2 * 2])
        vals = [v / 32768.0 for v in a]
    elif sw == 3:
        vals = []
        for i in range(0, len(raw) - 2, 3):
            v = raw[i] | (raw[i + 1] << 8) | (raw[i + 2] << 16)
            if v & 0x800000:
                v -= 0x1000000
            vals.append(v / 8388608.0)
    elif sw == 4:
        a = array.array("i")
        a.frombytes(raw[: len(raw) // 4 * 4])
        vals = [v / 2147483648.0 for v in a]
    else:
        print(f"[FAIL] 不支持的位深 {sw * 8} bit")
        return False

    if not vals:
        print("[FAIL] 空文件")
        return False

    peak = max(abs(v) for v in vals)
    rms = math.sqrt(sum(v * v for v in vals) / len(vals))
    dc = sum(vals) / len(vals)
    clip = sum(1 for v in vals if abs(v) >= 0.999)

    frames = len(vals) // ch
    head_frames = min(int(sr * 0.5), frames)
    head = vals[: head_frames * ch]
    head_rms = math.sqrt(sum(v * v for v in head) / len(head)) if head else 0.0

    print(f"峰值：{fmt_db(peak)}")
    print(f"整体 RMS：{fmt_db(rms)}")
    print(f"前 0.5 s 底噪 RMS：{fmt_db(head_rms)}")
    print(f"直流偏移：{dc:+.5f}")
    print(f"削波采样数（|x|≥0.999）：{clip}")

    ok = True
    if sr not in (48000, 44100):
        print(f"[WARN] 采样率 {sr} Hz 非 48k/44.1k，需要重采样（建议手机里直接设 48000）")
    if sw * 8 not in (16, 24, 32):
        print(f"[WARN] 位深 {sw * 8} bit 偏低")
    if clip > 0:
        print(f"[FAIL] 有 {clip} 个削波采样 → 必须降电平重录")
        ok = False
    if peak > 0.9:
        print(f"[WARN] 峰值 {fmt_db(peak)} 太接近 0 dBFS，建议录音距离拉远或降电平")
    elif peak < 0.03:
        print(f"[WARN] 峰值 {fmt_db(peak)} 太低（< -30 dBFS），信噪比会不够")
    if dur < 15:
        print(f"[WARN] 时长 {dur:.1f} s 偏短：基底素材需要 ≥60 s")
    print(f"[{'PASS' if ok else 'FAIL'}] {os.path.basename(path)}")
    return ok


def main(argv):
    targets = []
    for a in argv[1:]:
        if os.path.isdir(a):
            targets += [
                os.path.join(a, f)
                for f in sorted(os.listdir(a))
                if f.lower().endswith((".wav", ".m4a", ".mp3", ".aac", ".flac", ".ogg", ".opus"))
            ]
        else:
            targets.append(a)
    if not targets:
        print(__doc__)
        return 2
    results = [inspect(t) for t in targets]
    print("=" * 74)
    print(f"合计 {len(results)} 个文件，通过 {sum(1 for r in results if r)} 个")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
