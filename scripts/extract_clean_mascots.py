import os
import cv2
import numpy as np
from PIL import Image

UI_DIR = os.path.join('docs', 'archive', 'UI') if os.path.exists(os.path.join('docs', 'archive', 'UI')) else 'UI'

def process_navy():
    print("=== Extracting NAVY (Native Transparent Die-Cuts) ===")
    img = Image.open(os.path.join(UI_DIR, 'Blue Camera Cat Mascot Sticker Sheet.png'))
    out_dir = os.path.join('frontend', 'public', 'mascot', 'navy')
    os.makedirs(out_dir, exist_ok=True)
    
    boxes = [
        (60, 455, 20, 380),    # 1. Hello
        (60, 455, 380, 750),   # 2. Looking around
        (60, 455, 750, 1140),  # 3. Pointing
        (60, 455, 1140, 1530), # 4. Excited
        (530, 870, 20, 420),   # 5. Working
        (530, 875, 420, 800),  # 6. Done!
        (530, 875, 800, 1130), # 7. Leaving
        (530, 868, 1130, 1530) # 8. Idle
    ]
    
    for idx, (y1, y2, x1, x2) in enumerate(boxes, 1):
        sub = img.crop((x1, y1, x2, y2))
        bbox = sub.getbbox()
        tight = sub.crop(bbox)
        save_path = os.path.join(out_dir, f'pose{idx}.png')
        tight.save(save_path)
        print(f"  [navy] Pose {idx}: {tight.size[0]}x{tight.size[1]} transparent PNG")

def process_dark():
    print("=== Extracting DARK (Transparent Background & Effects) ===")
    sheet = cv2.imread(os.path.join(UI_DIR, 'Grainy Cat Mascot Tutorial Sheet.png'))
    out_dir = os.path.join('frontend', 'public', 'mascot', 'dark')
    os.makedirs(out_dir, exist_ok=True)
    
    regions = [
        (60, 455, 20, 380),    # 1. Hello
        (60, 438, 380, 750),   # 2. Looking around
        (60, 458, 750, 1140),  # 3. Pointing
        (60, 438, 1140, 1530), # 4. Excited
        (530, 872, 20, 420),   # 5. Working
        (530, 878, 420, 800),  # 6. Done!
        (530, 880, 800, 1130), # 7. Leaving
        (530, 868, 1130, 1530) # 8. Idle
    ]
    
    for idx, (y1, y2, x1, x2) in enumerate(regions, 1):
        crop = sheet[y1:y2, x1:x2].copy()
        ch, cw = crop.shape[:2]
        
        mask = np.zeros((ch, cw), np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        mask[:12, :] = cv2.GC_BGD
        mask[-12:, :] = cv2.GC_BGD
        mask[:, :12] = cv2.GC_BGD
        mask[:, -12:] = cv2.GC_BGD
        
        mask[15:ch-15, 15:cw-15] = cv2.GC_PR_FGD
        # Vertical strip covering head through body
        cy, cx = ch // 2, cw // 2
        mask[int(ch*0.2):int(ch*0.85), int(cw*0.25):int(cw*0.75)] = cv2.GC_FGD
        
        cv2.grabCut(crop, mask, None, bgdModel, fgdModel, 6, cv2.GC_INIT_WITH_MASK)
        fg_mask = np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD), 1, 0).astype('uint8')
        
        # Include bright chalk/sparks
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        sparks = (gray > 52) & (mask != cv2.GC_BGD)
        fg_mask = cv2.bitwise_or(fg_mask, sparks.astype(np.uint8))
        
        # Connected components filter to eliminate isolated speckles
        nb, out, stats, _ = cv2.connectedComponentsWithStats(fg_mask)
        clean_mask = np.zeros((ch, cw), dtype=np.uint8)
        for i in range(1, nb):
            if stats[i, cv2.CC_STAT_AREA] > 35:
                clean_mask[out == i] = 1
                
        rgba = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
        rgba[clean_mask == 0, 3] = 0
        
        ys, xs = np.where(clean_mask > 0)
        if len(ys) > 0 and len(xs) > 0:
            tight = rgba[ys.min():ys.max()+1, xs.min():xs.max()+1]
        else:
            tight = rgba
            
        save_path = os.path.join(out_dir, f'pose{idx}.png')
        cv2.imwrite(save_path, tight)
        print(f"  [dark] Pose {idx}: {tight.shape[1]}x{tight.shape[0]} transparent PNG")

def process_paper():
    print("=== Extracting PAPER (Checkerboard Removed & Transparent Die-Cuts) ===")
    guide = cv2.imread(os.path.join(UI_DIR, 'Camera Cat Mascot Sticker Guide.png'))
    out_dir = os.path.join('frontend', 'public', 'mascot', 'paper')
    os.makedirs(out_dir, exist_ok=True)
    
    regions = [
        (35, 422, 20, 420),     # 1. Hello
        (35, 422, 420, 820),    # 2. Looking around
        (35, 422, 820, 1260),   # 3. Pointing
        (35, 422, 1260, 1720),  # 4. Excited
        (540, 835, 20, 460),    # 5. Working
        (540, 835, 460, 880),   # 6. Done!
        (540, 835, 880, 1260),  # 7. Leaving
        (540, 835, 1260, 1720)  # 8. Idle
    ]
    
    for idx, (y1, y2, x1, x2) in enumerate(regions, 1):
        crop = guide[y1:y2, x1:x2].copy()
        ch, cw = crop.shape[:2]
        
        mask = np.zeros((ch, cw), np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        mask[:8, :] = cv2.GC_BGD
        mask[-8:, :] = cv2.GC_BGD
        mask[:, :8] = cv2.GC_BGD
        mask[:, -8:] = cv2.GC_BGD
        
        mask[10:ch-10, 10:cw-10] = cv2.GC_PR_FGD
        cy, cx = ch // 2, cw // 2
        mask[int(ch*0.2):int(ch*0.8), int(cw*0.25):int(cw*0.75)] = cv2.GC_FGD
        
        cv2.grabCut(crop, mask, None, bgdModel, fgdModel, 6, cv2.GC_INIT_WITH_MASK)
        fg_mask = np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD), 1, 0).astype('uint8')
        
        # Include sparks/Zs/action marks that may have high color saturation
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        # Orange/yellow sparks have sat > 80
        color_effects = (hsv[:, :, 1] > 75) & (mask != cv2.GC_BGD)
        fg_mask = cv2.bitwise_or(fg_mask, color_effects.astype(np.uint8))
        
        nb, out, stats, _ = cv2.connectedComponentsWithStats(fg_mask)
        clean_mask = np.zeros((ch, cw), dtype=np.uint8)
        for i in range(1, nb):
            if stats[i, cv2.CC_STAT_AREA] > 35:
                clean_mask[out == i] = 1
                
        rgba = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
        rgba[clean_mask == 0, 3] = 0
        
        ys, xs = np.where(clean_mask > 0)
        if len(ys) > 0 and len(xs) > 0:
            tight = rgba[ys.min():ys.max()+1, xs.min():xs.max()+1]
        else:
            tight = rgba
            
        save_path = os.path.join(out_dir, f'pose{idx}.png')
        cv2.imwrite(save_path, tight)
        print(f"  [paper] Pose {idx}: {tight.shape[1]}x{tight.shape[0]} transparent PNG")

def process_branding():
    print("=== Extracting CatLog Branding Assets ===")
    # 1. Full Logo Lockup
    logo_src = cv2.imread('scratch/catlog_logo_full.png', cv2.IMREAD_UNCHANGED)
    cv2.imwrite('frontend/public/catlog-logo.png', logo_src)
    print("  Saved frontend/public/catlog-logo.png")
    
    # 2. Square Cat Head Icon & Favicon
    icon_src = cv2.imread('scratch/catlog_icon.png', cv2.IMREAD_UNCHANGED)
    cv2.imwrite('frontend/public/catlog-icon.png', icon_src)
    cv2.imwrite('frontend/public/favicon.png', icon_src)
    # Also copy to frontend/src/assets/ if desired
    os.makedirs('frontend/src/assets', exist_ok=True)
    cv2.imwrite('frontend/src/assets/catlog-icon.png', icon_src)
    cv2.imwrite('frontend/src/assets/catlog-logo.png', logo_src)
    print("  Saved frontend/public/catlog-icon.png and favicon.png")
    
    # 3. Tagline Banner
    tagline_src = cv2.imread('scratch/catlog_tagline.png', cv2.IMREAD_UNCHANGED)
    cv2.imwrite('frontend/public/catlog-tagline.png', tagline_src)
    cv2.imwrite('frontend/src/assets/catlog-tagline.png', tagline_src)
    print("  Saved frontend/public/catlog-tagline.png")

if __name__ == '__main__':
    process_navy()
    process_dark()
    process_paper()
    process_branding()
    print("SUCCESS: All 24 mascot poses and branding assets cleanly exported!")
