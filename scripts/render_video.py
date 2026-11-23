import os
import sys
import json
import asyncio
import subprocess
import argparse
import edge_tts

async def synthesize_dialogue(lines, temp_dir):
    audio_segments = []
    for idx, d in enumerate(lines):
        voice = d.get("voice", "hi-IN-MadhurNeural")
        text = d.get("text", "")
        fn = os.path.join(temp_dir, f"turn_{idx:03d}.mp3")
        tts = edge_tts.Communicate(text, voice, rate="+4%", pitch="+0Hz")
        await tts.save(fn)
        audio_segments.append(fn)
    return audio_segments

def concat_audios(audio_files, out_audio, temp_dir):
    list_path = os.path.join(temp_dir, "concat_audio.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for a in audio_files:
            abs_a = os.path.abspath(a).replace("\\", "/")
            f.write(f"file '{abs_a}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", out_audio], check=True, capture_output=True)
    if os.path.exists(list_path):
        os.remove(list_path)

def create_slide_video(slide_img, slide_audio, out_video):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", slide_img,
        "-i", slide_audio,
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest", out_video
    ]
    subprocess.run(cmd, check=True, capture_output=True)

async def render_chapter(chapter_name, base_dir="."):
    ch_dir = os.path.join(base_dir, "chapters", chapter_name)
    script_path = os.path.join(ch_dir, "script.json")
    slides_dir = os.path.join(ch_dir, "slides")
    build_dir = os.path.join(ch_dir, "build")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    slide_videos = []
    total_slides = len(data["slides"])
    print(f"=== Rendering {chapter_name} ({total_slides} slides) ===")

    for slide in data["slides"]:
        s_num = slide["slide_num"]
        s_img = os.path.join(slides_dir, slide["slide_image"])
        print(f"--> Processing Slide {s_num:02d} / {total_slides}...")

        slide_temp = os.path.join(build_dir, f"slide_{s_num:02d}")
        os.makedirs(slide_temp, exist_ok=True)

        audio_parts = await synthesize_dialogue(slide["dialogue"], slide_temp)
        slide_audio = os.path.join(build_dir, f"audio_slide_{s_num:02d}.mp3")
        concat_audios(audio_parts, slide_audio, slide_temp)

        slide_video = os.path.join(build_dir, f"video_slide_{s_num:02d}.mp4")
        create_slide_video(s_img, slide_audio, slide_video)
        slide_videos.append(slide_video)

        # clean slide temp turn files
        for p in audio_parts:
            if os.path.exists(p):
                os.remove(p)

    # Concat all slide videos into final marathon video
    print("=== Assembling Final Marathon Video ===")
    final_list = os.path.join(build_dir, "final_video_list.txt")
    with open(final_list, "w", encoding="utf-8") as f:
        for v in slide_videos:
            abs_v = os.path.abspath(v).replace("\\", "/")
            f.write(f"file '{abs_v}'\n")

    final_output = os.path.join(output_dir, f"{chapter_name}_Complete_Marathon.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_list, "-c", "copy", final_output], check=True)
    print(f"SUCCESS: Master Marathon Video generated at: {final_output}")
    print(f"File size: {os.path.getsize(final_output) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", default="chapter_01", help="Chapter folder name")
    args = parser.parse_args()
    asyncio.run(render_chapter(args.chapter))
