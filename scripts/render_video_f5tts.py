import os
import sys
import json
import subprocess
import argparse
import torch

try:
    from f5_tts.api import F5TTS
    F5_AVAILABLE = True
except ImportError:
    F5_AVAILABLE = False
    print("Warning: f5_tts package not installed. Run `pip install f5-tts` to use F5-TTS GPU voice cloning.")

def get_device():
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def synthesize_f5tts(f5_model, dialogue, temp_dir, voices_dir):
    audio_segments = []
    
    # Load reference files
    # Cloned from YouTube educator: https://youtu.be/IIR3FRCyO-s
    rohan_ref = os.path.join(voices_dir, "pw_teacher_ref.wav")
    rohan_txt = open(os.path.join(voices_dir, "pw_teacher_ref.txt"), "r", encoding="utf-8").read().strip()
    
    priya_ref = os.path.join(voices_dir, "priya_female_ref.wav")
    priya_txt = open(os.path.join(voices_dir, "priya_female_ref.txt"), "r", encoding="utf-8").read().strip()

    for idx, d in enumerate(dialogue):
        speaker = d.get("speaker", "Rohan")
        text = d.get("text", "")
        out_wav = os.path.join(temp_dir, f"turn_{idx:03d}.wav")

        if speaker.lower() == "priya":
            ref_audio = priya_ref
            ref_text = priya_txt
        else:
            ref_audio = rohan_ref
            ref_text = rohan_txt

        print(f"    [{speaker}] Synthesizing with F5-TTS GPU: \"{text[:45]}...\"")
        wav, sr, spec = f5_model.infer(
            ref_file=ref_audio,
            ref_text=ref_text,
            gen_text=text,
            file_wave=out_wav
        )
        audio_segments.append(out_wav)

    return audio_segments

def concat_audios(audio_files, out_audio, temp_dir):
    list_path = os.path.join(temp_dir, "concat_audio.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for a in audio_files:
            abs_a = os.path.abspath(a).replace("\\", "/")
            f.write(f"file '{abs_a}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c:a", "pcm_s16le", out_audio], check=True, capture_output=True)
    if os.path.exists(list_path):
        os.remove(list_path)

def create_slide_video(slide_img, slide_audio, out_video, use_gpu_nvenc=True):
    # If GPU is available and nvenc is supported, use h264_nvenc for ultra-fast rendering
    vcodec = "h264_nvenc" if use_gpu_nvenc and torch.cuda.is_available() else "libx264"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", slide_img,
        "-i", slide_audio,
        "-c:v", vcodec,
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest", out_video
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Fallback to libx264 if nvenc is not available in ffmpeg build
        cmd[cmd.index(vcodec)] = "libx264"
        cmd.insert(cmd.index("libx264") + 1, "-tune")
        cmd.insert(cmd.index("-tune") + 1, "stillimage")
        subprocess.run(cmd, check=True, capture_output=True)

def render_chapter_f5tts(chapter_name, base_dir="."):
    ch_dir = os.path.join(base_dir, "chapters", chapter_name)
    script_path = os.path.join(ch_dir, "script.json")
    slides_dir = os.path.join(ch_dir, "slides")
    voices_dir = os.path.join(base_dir, "voices")
    build_dir = os.path.join(ch_dir, "build_f5tts")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    device = get_device()
    print(f"=== Initializing F5-TTS on {device.upper()} (Zero-Shot Flow Matching Neural Voice) ===")
    f5_model = F5TTS(device=device)

    slide_videos = []
    total_slides = len(data["slides"])
    print(f"=== Rendering {chapter_name} ({total_slides} slides with Ultra-Realistic Human Voices) ===")

    for slide in data["slides"]:
        s_num = slide["slide_num"]
        s_img = os.path.join(slides_dir, slide["slide_image"])
        print(f"\n--> Slide {s_num:02d} / {total_slides} ({len(slide['dialogue'])} turns)...")

        slide_temp = os.path.join(build_dir, f"slide_{s_num:02d}")
        os.makedirs(slide_temp, exist_ok=True)

        audio_parts = synthesize_f5tts(f5_model, slide["dialogue"], slide_temp, voices_dir)
        slide_audio = os.path.join(build_dir, f"audio_slide_{s_num:02d}.wav")
        concat_audios(audio_parts, slide_audio, slide_temp)

        slide_video = os.path.join(build_dir, f"video_slide_{s_num:02d}.mp4")
        create_slide_video(s_img, slide_audio, slide_video, use_gpu_nvenc=(device == "cuda"))
        slide_videos.append(slide_video)

        # clean slide temp turn files
        for p in audio_parts:
            if os.path.exists(p):
                os.remove(p)

    # Concat all slide videos into final marathon video
    print("\n=== Assembling Final F5-TTS Master Marathon Video ===")
    final_list = os.path.join(build_dir, "final_video_list.txt")
    with open(final_list, "w", encoding="utf-8") as f:
        for v in slide_videos:
            abs_v = os.path.abspath(v).replace("\\", "/")
            f.write(f"file '{abs_v}'\n")

    final_output = os.path.join(output_dir, f"{chapter_name}_HumanVoice_F5TTS_Marathon.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_list, "-c", "copy", final_output], check=True)
    print(f"\n🎉 SUCCESS: Human-Voice Marathon Video generated at: {final_output}")
    print(f"File size: {os.path.getsize(final_output) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", default="chapter_01", help="Chapter folder name")
    args = parser.parse_args()
    render_chapter_f5tts(args.chapter)
