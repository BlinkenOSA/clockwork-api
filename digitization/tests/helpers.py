from digitization.models import DigitalVersion


def make_digital_version_container(container, **kwargs):
    defaults = {
        "container": container,
    }
    defaults.update(kwargs)
    return DigitalVersion.objects.create(**defaults)


def make_digital_version_finding_aids(finding_aids, **kwargs):
    defaults = {
        "finding_aids_entity": finding_aids,
    }
    defaults.update(kwargs)
    return DigitalVersion.objects.create(**defaults)


def get_tech_md():
    return '''{
    "streams": [
        {
            "index": 0,
            "codec_name": "ffv1",
            "codec_long_name": "FFmpeg video codec #1",
            "codec_type": "video",
            "codec_time_base": "1/25",
            "codec_tag_string": "FFV1",
            "codec_tag": "0x31564646",
            "width": 720,
            "height": 576,
            "coded_width": 720,
            "coded_height": 576,
            "has_b_frames": 0,
            "pix_fmt": "yuv422p10le",
            "level": -99,
            "refs": 1,
            "r_frame_rate": "25/1",
            "avg_frame_rate": "25/1",
            "time_base": "1/25",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 22625,
            "duration": "905.000000",
            "bit_rate": "86382323",
            "bits_per_raw_sample": "10",
            "nb_frames": "22625",
            "disposition": {
                "default": 0,
                "dub": 0,
                "original": 0,
                "comment": 0,
                "lyrics": 0,
                "karaoke": 0,
                "forced": 0,
                "hearing_impaired": 0,
                "visual_impaired": 0,
                "clean_effects": 0,
                "attached_pic": 0,
                "timed_thumbnails": 0
            }
        },
        {
            "index": 1,
            "codec_name": "pcm_s16le",
            "codec_long_name": "PCM signed 16-bit little-endian",
            "codec_type": "audio",
            "codec_time_base": "1/96000",
            "codec_tag_string": "[1][0][0][0]",
            "codec_tag": "0x0001",
            "sample_fmt": "s16",
            "sample_rate": "96000",
            "channels": 2,
            "bits_per_sample": 16,
            "r_frame_rate": "0/0",
            "avg_frame_rate": "0/0",
            "time_base": "1/96000",
            "start_pts": 0,
            "start_time": "0.000000",
            "bit_rate": "3072000",
            "nb_frames": "86880446",
            "disposition": {
                "default": 0,
                "dub": 0,
                "original": 0,
                "comment": 0,
                "lyrics": 0,
                "karaoke": 0,
                "forced": 0,
                "hearing_impaired": 0,
                "visual_impaired": 0,
                "clean_effects": 0,
                "attached_pic": 0,
                "timed_thumbnails": 0
            }
        }
    ],
    "format": {
        "filename": "/root/data/Content/Preservation/HU_OSA_00007083.avi",
        "nb_streams": 2,
        "nb_programs": 0,
        "format_name": "avi",
        "format_long_name": "AVI (Audio Video Interleaved)",
        "start_time": "0.000000",
        "duration": "905.000000",
        "size": "10120280744",
        "bit_rate": "89461045",
        "probe_score": 100
    }
}'''