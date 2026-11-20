#!/usr/bin/env python3
"""Build the gta6-clipper-01 vertical clip (720x1280, ~36s).

Creative decision (made in this session):
- Hook (24s): the 5 most watchable moments of Rockstar's official GTA VI
  Launch Trailer (Oct 15, 2026, downloaded from Rockstar's own CDN):
  red sports car, Lucia in the convertible, Vice City street, Jason & Lucia
  sunset embrace, night sniper. Vertical centre-crop, original trailer audio.
- Pitch (12s): OUT NOW skyline end-card, darkened, with the make.fun pitch
  as big on-screen text + English voiceover (TTS), trailer audio ducked.
  Text: "MAKE CLIPS LIKE THIS WITH AI AND EARN MONEY ON make.fun"
  + "make.fun/bounty/gta6-clipper-01".
Output: ~/workspace/gta6-clipper-01/clip/gta6-makefun-clip.mp4
"""
import os, subprocess, sys

BASE = os.path.expanduser("~/workspace/gta6-clipper-01/clip")
SRC = os.path.join(BASE, "launch-trailer.mp4")
VO = os.path.join(BASE, "voiceover.mp3")
OUT = os.path.join(BASE, "gta6-makefun-clip.mp4")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

HOOK = [(18, 23), (24, 29), (44, 49), (60, 64), (64, 69)]  # (start, end) seconds
PITCH_START, PITCH_END = 75, 87  # 12s skyline / end-card

def run(cmd, **kw):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)

def main():
    # 1. Voiceover (English, TTS Aria)
    vo_text = ("GTA 6 is out now. But here's the real cheat code. "
               "Make clips like this with AI, and earn money on make.fun.")
    if not os.path.exists(VO):
        run(["/opt/hatch/bin/tts", "speak", "--language", "en",
             "--voice", "avocado_v2:MAI_03", "--speed", "95",
             "--text", vo_text, "--output", VO])

    # 2. Hook segments: trim + vertical centre-crop + scale 720x1280
    segs = []
    for i, (s, e) in enumerate(HOOK):
        seg = os.path.join(BASE, f"hook_{i}.mp4")
        segs.append(seg)
        if not os.path.exists(seg):
            vf = "crop=1215:2160:1312:0,scale=720:1280"
            if i == 0:
                vf += (f",drawtext=fontfile={FONT}:text='GTA 6 IS OUT NOW':"
                       f"fontsize=58:fontcolor=white:borderw=3:bordercolor=black:"
                       f"x=(w-text_w)/2:y=120:enable='between(t,0,3)'")
            run(["ffmpeg", "-y", "-v", "error", "-ss", str(s), "-to", str(e),
                 "-i", SRC,
                 "-vf", vf,
                 "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                 "-c:a", "aac", "-b:a", "128k", seg])

    # concat hook
    lst = os.path.join(BASE, "hook_list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    hook = os.path.join(BASE, "hook.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", hook])

    # 3. Pitch segment: skyline 75-87s, darkened, drawtext lines, ducked audio + VO
    pitch_v = os.path.join(BASE, "pitch_v.mp4")
    draw = (
        f"drawbox=x=0:y=430:w=720:h=420:color=black@0.55:t=fill,"
        f"drawtext=fontfile={FONT}:text='MAKE CLIPS LIKE THIS':fontsize=52:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=450:enable='between(t,0,4)',"
        f"drawtext=fontfile={FONT}:text='WITH AI AND':fontsize=52:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=560:enable='between(t,0,4)',"
        f"drawtext=fontfile={FONT}:text='EARN MONEY':fontsize=72:fontcolor=#FFD700:borderw=3:bordercolor=black:x=(w-text_w)/2:y=450:enable='between(t,4,8)',"
        f"drawtext=fontfile={FONT}:text='ON make.fun':fontsize=72:fontcolor=#FFD700:borderw=3:bordercolor=black:x=(w-text_w)/2:y=560:enable='between(t,4,8)',"
        f"drawtext=fontfile={FONT}:text='make.fun/bounty':fontsize=44:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=480:enable='between(t,8,12)',"
        f"drawtext=fontfile={FONT}:text='gta6-clipper-01':fontsize=44:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=540:enable='between(t,8,12)'"
    )
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(PITCH_START), "-to", str(PITCH_END),
         "-i", SRC, "-i", VO,
         "-filter_complex",
         f"[0:v]crop=1215:2160:1312:0,scale=720:1280,eq=brightness=-0.25,{draw}[v];"
         f"[0:a]volume=0.15[a0];[1:a]adelay=500|500,volume=1.0[a1];[a0][a1]amix=inputs=2:duration=first[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast",
         "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-t", "12", pitch_v])

    # 4. Final concat: hook + pitch (same codecs/dims, stream copy via concat)
    final_list = os.path.join(BASE, "final_list.txt")
    with open(final_list, "w") as f:
        f.write(f"file '{hook}'\nfile '{pitch_v}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", final_list, "-c", "copy", OUT])

    # 5. Verify
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration,size", "-show_entries",
                          "stream=width,height,codec_name",
                          "-of", "default=noprint_wrappers=1", OUT],
                         capture_output=True, text=True, check=True)
    print(out.stdout)
    print("DONE:", OUT)

if __name__ == "__main__":
    main()
