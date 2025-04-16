import argparse
import os
import os.path as osp
import numpy as np
import cv2
import torch
import gc
import sys
from pathlib import Path

# 设置 Hydra 环境变量以获取完整错误信息
os.environ["HYDRA_FULL_ERROR"] = "1"

# 设置导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # samurai_master 目录

# 将 samurai_master 目录添加到 Python 路径
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 将 sam2 目录添加到 Python 路径
sam2_dir = os.path.join(parent_dir, "sam2")
if sam2_dir not in sys.path:
    sys.path.insert(0, sam2_dir)

# 将内部 sam2 目录添加到 Python 路径
sam2_inner_dir = os.path.join(sam2_dir, "sam2")
if sam2_inner_dir not in sys.path:
    sys.path.insert(0, sam2_inner_dir)

# 设置 Hydra 配置路径
os.environ["HYDRA_CONFIG_PATH"] = os.path.join(parent_dir, "sam2", "sam2", "configs")

# 直接从内部 sam2 目录导入
from build_sam import build_sam2_video_predictor

color = [(255, 0, 0)]

def load_txt(gt_path):
    with open(gt_path, 'r') as f:
        gt = f.readlines()
    prompts = {}
    for fid, line in enumerate(gt):
        x, y, w, h = map(float, line.split(','))
        x, y, w, h = int(x), int(y), int(w), int(h)
        prompts[fid] = ((x, y, x + w, y + h), 0)
    return prompts

def determine_model_cfg(model_path):
    # 使用绝对路径
    config_base = os.path.join(parent_dir, "sam2", "sam2", "configs", "samurai")
    if "large" in model_path or "_l" in model_path:
        return os.path.join(config_base, "sam2.1_hiera_l.yaml")
    elif "base_plus" in model_path or "_b+" in model_path:
        return os.path.join(config_base, "sam2.1_hiera_b+.yaml")
    elif "base" in model_path or "_b" in model_path:
        return os.path.join(config_base, "sam2.1_hiera_b+.yaml")
    elif "small" in model_path or "_s" in model_path:
        return os.path.join(config_base, "sam2.1_hiera_s.yaml")
    elif "tiny" in model_path or "_t" in model_path:
        return os.path.join(config_base, "sam2.1_hiera_t.yaml")
    else:
        return os.path.join(config_base, "sam2.1_hiera_b+.yaml")

def prepare_frames_or_path(video_path):
    if video_path.endswith(".mp4") or osp.isdir(video_path):
        return video_path
    else:
        raise ValueError("Invalid video_path format. Should be .mp4 or a directory of jpg frames.")

def main(args):
    # 修改输出目录路径计算
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             'samurai_django', 'myproject', 'media', 'processed_videos')
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用输入视频的文件名，但加上 "_processed" 后缀
    input_filename = os.path.basename(args.video_path)
    output_filename = os.path.splitext(input_filename)[0] + "_processed" + os.path.splitext(input_filename)[1]
    args.output_path = os.path.join(output_dir, output_filename)
    args.video_output_path = args.output_path  # 直接使用最终路径
    
    if not os.path.isabs(args.model_path):
        args.model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     "sam2", "checkpoints", os.path.basename(args.model_path))
    
    if not os.path.exists(args.model_path):
        raise FileNotFoundError(f"模型文件不存在: {args.model_path}")
    
    model_cfg = determine_model_cfg(args.model_path)
    predictor = build_sam2_video_predictor(model_cfg, args.model_path, device="cuda:0")
    frames_or_path = prepare_frames_or_path(args.video_path)
    prompts = load_txt(args.txt_path)

    frame_rate = 30
    if args.save_to_video:
        if osp.isdir(args.video_path):
            frames = sorted([osp.join(args.video_path, f) for f in os.listdir(args.video_path) if f.endswith((".jpg", ".jpeg", ".JPG", ".JPEG"))])
            loaded_frames = [cv2.imread(frame_path) for frame_path in frames]
            height, width = loaded_frames[0].shape[:2]
        else:
            cap = cv2.VideoCapture(args.video_path)
            frame_rate = cap.get(cv2.CAP_PROP_FPS)
            loaded_frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                loaded_frames.append(frame)
            cap.release()
            height, width = loaded_frames[0].shape[:2]

            if len(loaded_frames) == 0:
                raise ValueError("No frames were loaded from the video.")

    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(args.video_output_path, fourcc, frame_rate, (width, height))

    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        state = predictor.init_state(frames_or_path, offload_video_to_cpu=True)
        bbox, track_label = prompts[0]
        _, _, masks = predictor.add_new_points_or_box(state, box=bbox, frame_idx=0, obj_id=0)

        for frame_idx, object_ids, masks in predictor.propagate_in_video(state):
            mask_to_vis = {}
            bbox_to_vis = {}

            for obj_id, mask in zip(object_ids, masks):
                mask = mask[0].cpu().numpy()
                mask = mask > 0.0
                non_zero_indices = np.argwhere(mask)
                if len(non_zero_indices) == 0:
                    bbox = [0, 0, 0, 0]
                else:
                    y_min, x_min = non_zero_indices.min(axis=0).tolist()
                    y_max, x_max = non_zero_indices.max(axis=0).tolist()
                    bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
                bbox_to_vis[obj_id] = bbox
                mask_to_vis[obj_id] = mask

            if args.save_to_video:
                img = loaded_frames[frame_idx]
                for obj_id, mask in mask_to_vis.items():
                    mask_img = np.zeros((height, width, 3), np.uint8)
                    mask_img[mask] = color[(obj_id + 1) % len(color)]
                    img = cv2.addWeighted(img, 1, mask_img, 0.2, 0)

                for obj_id, bbox in bbox_to_vis.items():
                    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), color[obj_id % len(color)], 2)

                out.write(img)

        if args.save_to_video:
            out.release()

    del predictor, state
    gc.collect()
    torch.clear_autocast_cache()
    torch.cuda.empty_cache()

    try:
        # 不需要移动文件，因为已经直接保存在正确的位置
        if os.path.exists(args.output_path):
            print(f"处理完成，视频已保存到: {args.output_path}")
            # 返回相对于 media 目录的路径，方便前端访问
            relative_path = os.path.relpath(args.output_path, 
                                          os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                     'samurai_django', 'media'))
            return True, relative_path
        else:
            print(f"处理失败：找不到输出文件 {args.output_path}")
            return False, None

    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        return False, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='视频处理脚本')
    parser.add_argument('--video_path', type=str, required=True, help='输入视频路径')
    parser.add_argument('--txt_path', type=str, required=True, help='输入文本路径')
    # 移除 output_path 参数，因为现在使用固定的输出目录
    default_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    "sam2", "checkpoints", "sam2.1_hiera_base_plus.pt")
    parser.add_argument('--model_path', type=str, default=default_model_path, help='模型路径')
    parser.add_argument("--save_to_video", default=True, help="Save results to a video.")
    args = parser.parse_args()
    success, output_path = main(args)
    exit(0 if success else 1)
