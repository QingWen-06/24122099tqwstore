#!/usr/bin/env python3
"""随机声自动切分器：从一段连续录音里检测冲击事件（onset），逐条导出为独立资产。

典型用途：一次录一串键盘敲击 / 鼠标点击 / 门开关，自动切成每一下一条。

用法：
    python split_onsets.py --in 键盘1.wav --out-dir out --prefix KEY --dry-run
    python split_onsets.py --in 键盘1.wav --out-dir out --prefix KEY

参数：
    --thresh <dB>   高出噪声底多少 dB 判为事件，默认 8
    --min-gap <s>   两次事件最小间隔（间隔更近的合并为一次），默认 0.06
    --min-len <s>   事件最短长度，默认 0.015
    --pre <s>       事件起点前留多少，默认 0.010
    --post <s>      事件终点后留多少（尾音），默认 0.060
    --max-len <s>   单条上限，默认 2.0
    --peak <dBFS>   导出峰值，默认 -3
    --hp <Hz>       高通，默认 40
    --keep-stereo   保留立体声（默认也是立体声，单声道源会展开）
"""
import os
import sys
import array
import math
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_assets import (  # noqa: E402
    read_pcm, write_pcm24, biquad, resample, to_stereo,
    fade, apply_gain, db, peak_of, rms_of, remove_dc, SR_OUT,
)

DECIM = 4          # 包络计算时的抽样率降采样因子
WIN_S = 0.005      # 包络窗口 5ms


def envelope(chans, sr, decim=DECIM):
    """返回 (每个窗口的 RMS dB 列表, 窗口长度秒)。"""
    n = len(chans[0])
    hop = max(1, int(sr * WIN_S))
    win = hop
    outs = []
    step = decim
    for s in range(0, n - win + 1, win):
        acc = 0.0
        cnt = 0
        for c in chans:
            x = c
            for i in range(s, s + win, step):
                acc += x[i] * x[i]
                cnt += 1
        outs.append(db(math.sqrt(acc / cnt)) if cnt else -999.0)
    return outs, win / float(sr)


def percentile(vals, p):
    s = sorted(vals)
    if not s:
        return -999.0
    idx = int(len(s) * p)
    return s[min(idx, len(s) - 1)]


def detect(env, win_s, thresh_db, min_gap_s, min_len_s):
    floor = percentile(env, 0.20)
    # 绝对上限：找不到底噪时兜底
    thr = floor + thresh_db
    events = []
    inside = False
    start = 0
    for i, v in enumerate(env):
        if not inside and v > thr:
            inside = True
            start = i
        elif inside and v <= thr:
            events.append((start, i))
            inside = False
    if inside:
        events.append((start, len(env) - 1))

    # 合并靠得太近的
    merged = []
    for a, b in events:
        if merged and (a - merged[-1][1]) * win_s < min_gap_s:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    # 过滤太短的
    merged = [e for e in merged if (e[1] - e[0]) * win_s >= min_len_s]
    return floor, thr, merged


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--thresh", type=float, default=8.0)
    ap.add_argument("--min-gap", type=float, default=0.06)
    ap.add_argument("--min-len", type=float, default=0.015)
    ap.add_argument("--pre", type=float, default=0.010)
    ap.add_argument("--post", type=float, default=0.060)
    ap.add_argument("--max-len", type=float, default=2.0)
    ap.add_argument("--peak", type=float, default=-3.0)
    ap.add_argument("--hp", type=float, default=40.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv[1:])

    nch, sr, chans = read_pcm(a.inp)
    dur = len(chans[0]) / sr
    print(f"[读入] {os.path.basename(a.inp)} {nch}ch {sr}Hz {dur:.2f}s "
          f"peak {db(peak_of(chans)):.1f} rms {db(rms_of(chans)):.1f}")

    env, win_s = envelope(chans, sr)
    floor, thr, events = detect(env, win_s, a.thresh, a.min_gap, a.min_len)
    print(f"[包络] 窗口 {win_s*1000:.0f}ms | 噪声底 {floor:.1f} dBFS | 触发阈值 {thr:.1f} dBFS")
    print(f"[检测] {len(events)} 个事件")

    if not a.dry_run:
        os.makedirs(a.out_dir, exist_ok=True)

    n_pre = int(a.pre * sr)
    n_post = int(a.post * sr)
    n_max = int(a.max_len * sr)
    exported = 0
    print(f"  {'#':>3} {'起点':>8} {'时长':>7} {'峰值':>9} {'RMS':>9}  文件")
    for idx, (s_i, e_i) in enumerate(events, 1):
        s = max(0, int(s_i * win_s * sr) - n_pre)
        e = min(len(chans[0]), int((e_i + 1) * win_s * sr) + n_post)
        if e - s > n_max:
            e = s + n_max
        seg = [array.array("d", c[s:e]) for c in chans]
        pk = db(peak_of(seg))
        rm = db(rms_of(seg))
        length = (e - s) / sr
        print(f"  {idx:>3} {s/sr:8.3f} {length:7.3f} {pk:9.1f} {rm:9.1f}", end="")
        if length < 0.03:
            print("  [跳过：太短]")
            continue
        name = f"{a.prefix}_{idx:02d}.wav"
        out = os.path.join(a.out_dir, name)
        print(f"  {name}")
        if a.dry_run:
            continue
        work = [array.array("d", c) for c in seg]
        remove_dc(work)
        if a.hp:
            biquad(work, sr, a.hp, kind="hp")
        work = resample(work, sr, SR_OUT)
        work = to_stereo(work, pseudo=True)
        fade(work, SR_OUT, 0.002, min(0.03, length / 3.0))
        apply_gain(work, 0.0, a.peak, 0.0)
        write_pcm24(out, SR_OUT, work)
        exported += 1

    print(f"[完成] {'预览' if a.dry_run else '导出'} {exported} 条资产"
          + (f" -> {a.out_dir}" if not a.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
