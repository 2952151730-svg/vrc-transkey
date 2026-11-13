import sys
import math
import time
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple, List, Dict
import openvr
from PIL import Image, ImageDraw
from config import config

MIN_WIDTH_M = 0.25
MAX_WIDTH_M = 0.85
DEFAULT_WIDTH_M = 0.42


class PIXELFORMATDESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ('nSize', wintypes.WORD),
        ('nVersion', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('iPixelType', wintypes.BYTE),
        ('cColorBits', wintypes.BYTE),
        ('cRedBits', wintypes.BYTE), ('cRedShift', wintypes.BYTE),
        ('cGreenBits', wintypes.BYTE), ('cGreenShift', wintypes.BYTE),
        ('cBlueBits', wintypes.BYTE), ('cBlueShift', wintypes.BYTE),
        ('cAlphaBits', wintypes.BYTE), ('cAlphaShift', wintypes.BYTE),
        ('cAccumBits', wintypes.BYTE),
        ('cAccumRedBits', wintypes.BYTE), ('cAccumGreenBits', wintypes.BYTE),
        ('cAccumBlueBits', wintypes.BYTE), ('cAccumAlphaBits', wintypes.BYTE),
        ('cDepthBits', wintypes.BYTE),
        ('cStencilBits', wintypes.BYTE),
        ('cAuxBuffers', wintypes.BYTE),
        ('iLayerType', wintypes.BYTE),
        ('bReserved', wintypes.BYTE),
        ('dwLayerMask', wintypes.DWORD),
        ('dwVisibleMask', wintypes.DWORD),
        ('dwDamageMask', wintypes.DWORD),
    ]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.c_size_t),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', ctypes.c_wchar * 260)
    ]


class GLTextureContext:
    """
    轻量级 Windows 原生 OpenGL 硬件加速上下文。
    直接在 GPU 显存内维护与更新纹理，彻底消除 SetOverlayRaw 带来的单帧黑屏闪烁与 IPC 队列拥堵。
    """
    def __init__(self, width: int = 1000, height: int = 560):
        self.width = width
        self.height = height
        self.tex_id = 0
        self.tex_ids = [0, 0]
        self.active_idx = 0
        self.hglrc = None
        self.hdc = None
        self.hwnd = None
        self.is_valid = False
        self._init_gl()

    def _init_gl(self):
        try:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            gl = ctypes.windll.opengl32

            user32.CreateWindowExW.argtypes = [
                wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
            ]
            user32.CreateWindowExW.restype = wintypes.HWND

            self.hwnd = user32.CreateWindowExW(0, 'STATIC', 'VRC_TransKey_GL', 0x80000000, 0, 0, 16, 16, 0, 0, 0, 0)
            if not self.hwnd:
                return

            self.hdc = user32.GetDC(self.hwnd)
            pfd = PIXELFORMATDESCRIPTOR()
            pfd.nSize = ctypes.sizeof(PIXELFORMATDESCRIPTOR)
            pfd.nVersion = 1
            # PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER = 4 | 32 | 1 = 37
            pfd.dwFlags = 37
            pfd.iPixelType = 0  # PFD_TYPE_RGBA
            pfd.cColorBits = 32
            pfd.cDepthBits = 16

            pf = gdi32.ChoosePixelFormat(self.hdc, ctypes.byref(pfd))
            gdi32.SetPixelFormat(self.hdc, pf, ctypes.byref(pfd))

            self.hglrc = gl.wglCreateContext(self.hdc)
            gl.wglMakeCurrent(self.hdc, self.hglrc)

            tex_buf = (ctypes.c_uint * 2)()
            gl.glGenTextures(2, tex_buf)
            self.tex_ids = [int(tex_buf[0]), int(tex_buf[1])]
            self.active_idx = 0
            self.tex_id = self.tex_ids[0]

            GL_TEXTURE_2D = 0x0DE1
            GL_TEXTURE_MIN_FILTER = 0x2801
            GL_TEXTURE_MAG_FILTER = 0x2800
            GL_LINEAR = 0x2601
            GL_CLAMP_TO_EDGE = 0x812F
            GL_TEXTURE_WRAP_S = 0x2802
            GL_TEXTURE_WRAP_T = 0x2803
            GL_RGBA = 0x1908
            GL_UNSIGNED_BYTE = 0x1401

            for tid in self.tex_ids:
                gl.glBindTexture(GL_TEXTURE_2D, tid)
                gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            gl.glFinish()

            self.is_valid = True
            print(f"[VROverlay] GPU 双缓冲纹理渲染就绪! Textures: {self.tex_ids}")
        except Exception as e:
            print(f"[VROverlay] GPU 加速初始化提示: {e}，将启用安全直传通道")
            self.is_valid = False

    def update_texture(self, raw_bytes: bytes, width: int, height: int) -> int:
        if not self.is_valid:
            return 0
        try:
            gl = ctypes.windll.opengl32
            if gl.wglGetCurrentContext() != self.hglrc:
                gl.wglMakeCurrent(self.hdc, self.hglrc)
            GL_TEXTURE_2D = 0x0DE1
            GL_RGBA = 0x1908
            GL_UNSIGNED_BYTE = 0x1401
            next_idx = 1 - self.active_idx
            target_tid = self.tex_ids[next_idx]
            gl.glBindTexture(GL_TEXTURE_2D, target_tid)
            gl.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, raw_bytes)
            gl.glFinish()
            self.active_idx = next_idx
            self.tex_id = target_tid
            return target_tid
        except Exception as e:
            print(f"[VROverlay] GPU 显存纹理写入警告: {e}")
            return 0

    def destroy(self):
        """释放 OpenGL 上下文、纹理与隐藏窗口句柄"""
        if not self.is_valid:
            return
        self.is_valid = False
        try:
            gl = ctypes.windll.opengl32
            user32 = ctypes.windll.user32
            if gl.wglGetCurrentContext() == self.hglrc:
                gl.wglMakeCurrent(0, 0)
            valid_tids = [t for t in self.tex_ids if t]
            if valid_tids:
                arr = (ctypes.c_uint * len(valid_tids))(*valid_tids)
                gl.glDeleteTextures(len(valid_tids), arr)
            if self.hglrc:
                gl.wglDeleteContext(self.hglrc)
                self.hglrc = None
            if self.hwnd and self.hdc:
                user32.ReleaseDC(self.hwnd, self.hdc)
                self.hdc = None
            if self.hwnd:
                user32.DestroyWindow(self.hwnd)
                self.hwnd = None
        except Exception:
            pass


class VROverlayManager:
    def __init__(self, key: str = "vrc.lightweight.transkey", name: str = "VRC TransKey"):
        self.key = key
        self.name = name
        self.vr_system = None
        self.vr_overlay = None

        # GPU 硬件加速原生纹理
        self.gl_ctx: Optional[GLTextureContext] = None
        self.ovr_texture: Optional[openvr.Texture_t] = None

        # 主键盘 Overlay、3D 激光光束 Overlay 与表面准星 Overlay
        # 即使在 Virtual Desktop (VD)、SteamLink、Pico 串流下也能完美显示激光引导线与落点准星！
        self.handle = None
        self.laser_handle = None
        self.cursor_handle = None

        # 当前面板物理宽度 (米)，严格限制在 [0.25, 0.85] 防止缩成一个点
        cfg_overlay = config.get("overlay", default={}) or {}
        raw_w = float(cfg_overlay.get("width_m", DEFAULT_WIDTH_M))
        self.width_m = max(MIN_WIDTH_M, min(MAX_WIDTH_M, raw_w))

        # 激光与准星显示状态机与环境模式
        # "auto": 仅检测到 Virtual Desktop 时开启(原生SteamVR防双线); "on": 强制开启; "off": 强制关闭
        self.laser_mode = cfg_overlay.get("laser_guide", "auto")
        self.is_vd_active = False
        self.is_laser_visible: bool = False
        self.last_laser_length: float = 0.0

        self._c_buf = None
        self.is_visible = False

        # 面板空间位姿矩阵与用户拖拽记忆状态
        self.current_transform = None
        self.last_spawn_hmd_pos: Optional[Tuple[float, float, float]] = None
        self.prev_hmd_activity: int = 0
        self.has_user_interacted: bool = False

        # 拖拽位置持久化记忆 (点 X 隐藏后再次呼出时回到拖拽后的位置)
        self.saved_world_pos: Optional[Tuple[float, float, float]] = None
        self.saved_hmd_pos: Optional[Tuple[float, float, float]] = None
        self.saved_hmd_fwd: Optional[Tuple[float, float]] = None
        self.saved_rel_offset: Optional[Tuple[float, float, float]] = None

        # 握把键 (Grip) 与面板拖拽状态：严格由中指侧面握柄触发，B 键/A 键绝不触发拖动！
        self.is_dragging = False
        self.drag_controller_idx: Optional[int] = None
        self.drag_by_grip = False
        self.drag_start_time = 0.0
        self.drag_start_ctrl_pos = (0.0, 0.0, 0.0)
        self.drag_start_panel_pos = (0.0, 0.0, 0.0)
        self.is_any_grip_pressed = False
        self.last_grip_active_time = 0.0

        # 控制器按键状态机
        self.prev_thumbstick_pressed: Dict[int, bool] = {}
        self.thumb_first_press_time: Dict[int, float] = {}
        self.thumb_released_after_first: Dict[int, bool] = {}
        self.prev_grip_pressed: Dict[int, bool] = {}
        self.prev_trigger_pressed: Dict[int, bool] = {}

        # 激光瞄准与悬停状态
        self.last_hover_xy = (500, 280)
        self.current_hover_xy: Optional[Tuple[int, int]] = None
        self.is_trigger_down_on_slider = False

        # 抬头字幕 HUD Overlay 状态
        self.hud_handle = None
        self.hud_gl_ctx = None
        self.hud_ovr_texture = None
        self.hud_visible = False
        self._vr_apps = None
        self._last_scene_check_ts = 0.0
        self._cached_in_scene = False

        self.init_openvr()

    def init_openvr(self):
        try:
            self.vr_system = openvr.init(openvr.VRApplication_Overlay)
            self.vr_overlay = openvr.IVROverlay()

            cfg_overlay = config.get("overlay", default={}) or {}
            alpha = float(cfg_overlay.get("alpha", 0.95))

            # 智能检测当前运行环境是否为 Virtual Desktop (VD) 串流
            self.is_vd_active = self._detect_virtual_desktop()
            if self.is_vd_active:
                print("[VROverlay] VR 运行时检测: Virtual Desktop (VD 串流环境) -> 已激活专属 3D 激光引导线")
            else:
                print("[VROverlay] VR 运行时检测: SteamVR 原生 / Link 环境 -> 隐藏第三方引导线以防手柄双线")

            # 1. 创建主键盘 Overlay
            self.handle = self.vr_overlay.createOverlay(self.key, self.name)
            self.vr_overlay.setOverlayWidthInMeters(self.handle, self.width_m)
            self.vr_overlay.setOverlayAlpha(self.handle, alpha)

            # 初始化 GPU 原生纹理硬件加速 (彻底根治打字闪烁)
            try:
                self.gl_ctx = GLTextureContext(1000, 560)
                if self.gl_ctx.is_valid:
                    self.ovr_texture = openvr.Texture_t()
                    self.ovr_texture.handle = ctypes.c_void_p(self.gl_ctx.tex_id)
                    self.ovr_texture.eType = openvr.TextureType_OpenGL
                    self.ovr_texture.eColorSpace = openvr.ColorSpace_Auto

                    bounds = openvr.VRTextureBounds_t()
                    bounds.uMin = 0.0
                    bounds.uMax = 1.0
                    bounds.vMin = 0.0
                    bounds.vMax = 1.0
                    self.vr_overlay.setOverlayTextureBounds(self.handle, bounds)
            except Exception as e:
                print(f"[VROverlay] GPU 纹理上下文绑定提示: {e}")

            # 启用多光标与抗抖动，但不抢占游戏输入焦点 (绝不调用 MakeOverlaysInteractiveIfVisible，彻底避免 VRC AFK)
            for flag_name in (
                "VROverlayFlags_EnableClickStabilization",
                "VROverlayFlags_MultiCursor",
                "VROverlayFlags_SortWithNonSceneOverlays",
            ):
                flag = getattr(openvr, flag_name, None)
                if flag is not None:
                    try:
                        self.vr_overlay.setOverlayFlag(self.handle, flag, True)
                    except Exception:
                        pass

            # 2. 创建 3D 激光光束 Overlay (解决 Virtual Desktop / VD 串流下没有引导线的问题)
            try:
                self.laser_handle = self.vr_overlay.createOverlay(self.key + ".laser", "VRC TransKey Laser")
                self._upload_laser_texture()
                self.vr_overlay.setOverlayAlpha(self.laser_handle, 0.88)
                self.vr_overlay.hideOverlay(self.laser_handle)
            except Exception as e:
                print(f"[VROverlay] 激光 Overlay 初始化失败: {e}")
                self.laser_handle = None

            # 3. 创建键盘表面悬停发光准星 Overlay
            try:
                self.cursor_handle = self.vr_overlay.createOverlay(self.key + ".cursor", "VRC TransKey Cursor")
                self._upload_cursor_texture()
                self.vr_overlay.setOverlayWidthInMeters(self.cursor_handle, 0.016)
                self.vr_overlay.setOverlayAlpha(self.cursor_handle, 0.95)
                self.vr_overlay.hideOverlay(self.cursor_handle)
            except Exception as e:
                print(f"[VROverlay] 准星 Overlay 初始化失败: {e}")
                self.cursor_handle = None

            # 4. 创建语音翻译 HUD 抬头显示 Overlay
            try:
                self.hud_handle = self.vr_overlay.createOverlay(self.key + ".hud", "VRC TransKey Voice HUD")
                self.vr_overlay.setOverlayWidthInMeters(self.hud_handle, 0.48)
                self.vr_overlay.setOverlayAlpha(self.hud_handle, 0.95)
                self.hud_gl_ctx = GLTextureContext(800, 180)
                if self.hud_gl_ctx.is_valid:
                    self.hud_ovr_texture = openvr.Texture_t()
                    self.hud_ovr_texture.handle = ctypes.c_void_p(self.hud_gl_ctx.tex_id)
                    self.hud_ovr_texture.eType = openvr.TextureType_OpenGL
                    self.hud_ovr_texture.eColorSpace = openvr.ColorSpace_Auto
                    h_bounds = openvr.VRTextureBounds_t()
                    h_bounds.uMin = 0.0
                    h_bounds.uMax = 1.0
                    h_bounds.vMin = 0.0
                    h_bounds.vMax = 1.0
                    self.vr_overlay.setOverlayTextureBounds(self.hud_handle, h_bounds)
                self.vr_overlay.hideOverlay(self.hud_handle)
            except Exception as e:
                print(f"[VROverlay] HUD Overlay 初始化失败: {e}")
                self.hud_handle = None

            print(f"[VROverlay] OpenVR Overlay 初始化成功! Handle: {self.handle}, 初始宽度: {self.width_m:.2f}m")
        except Exception as e:
            print(f"[VROverlay] 初始化 OpenVR 失败: {e}")
            self.vr_system = None
            self.vr_overlay = None

    def _upload_laser_texture(self):
        """生成 128x16 柔和青蓝发光激光束贴图"""
        if not self.laser_handle or not self.vr_overlay:
            return
        w, h = 128, 16
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            dist_center = abs(y - (h - 1) / 2.0) / (h / 2.0)
            alpha = int(max(0.0, (1.0 - dist_center ** 1.3)) * 240)
            if dist_center < 0.28:
                col = (220, 248, 255, alpha)
            else:
                col = (64, 165, 255, alpha)
            draw.line([(2, y), (w - 3, y)], fill=col)
        raw = img.tobytes()
        c_buf = (ctypes.c_char * len(raw)).from_buffer_copy(raw)
        self.vr_overlay.setOverlayRaw(self.laser_handle, c_buf, w, h, 4)

    def _upload_cursor_texture(self):
        """生成 32x32 发光圆环微型落点准星"""
        if not self.cursor_handle or not self.vr_overlay:
            return
        sz = 32
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((2, 2, sz - 3, sz - 3), fill=(50, 140, 255, 90), outline=(130, 210, 255, 240), width=2)
        draw.ellipse((10, 10, sz - 11, sz - 11), fill=(255, 255, 255, 250))
        raw = img.tobytes()
        c_buf = (ctypes.c_char * len(raw)).from_buffer_copy(raw)
        self.vr_overlay.setOverlayRaw(self.cursor_handle, c_buf, sz, sz, 4)

    def set_width_meters(self, new_width: float) -> float:
        """动态设置键盘物理宽度，严格限制在 [MIN_WIDTH_M, MAX_WIDTH_M] 范围内"""
        clamped = round(max(MIN_WIDTH_M, min(MAX_WIDTH_M, float(new_width))), 2)
        self.width_m = clamped
        if self.vr_overlay and self.handle:
            try:
                self.vr_overlay.setOverlayWidthInMeters(self.handle, clamped)
            except Exception:
                pass
        return clamped

    def _set_transform(self, mat: openvr.HmdMatrix34_t):
        self.current_transform = mat
        if self.vr_overlay and self.handle:
            try:
                self.vr_overlay.setOverlayTransformAbsolute(self.handle, openvr.TrackingUniverseStanding, mat)
            except Exception:
                pass

    def _get_hmd_horizontal_frame(self):
        """获取当前头显位置 (px, py, pz)、水平前向单位向量 (fx, fz)、水平右向单位向量 (rx, rz)"""
        if not self.vr_system:
            return None
        poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
        poses = poses_t()
        self.vr_system.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0.0, poses)
        hp = poses[openvr.k_unTrackedDeviceIndex_Hmd]
        if not hp.bPoseIsValid:
            return None
        m = hp.mDeviceToAbsoluteTracking
        px, py, pz = m[0][3], m[1][3], m[2][3]
        fx, fz = -m[0][2], -m[2][2]
        fl = math.sqrt(fx * fx + fz * fz)
        if fl > 0.001:
            fx /= fl
            fz /= fl
        else:
            fx, fz = 0.0, -1.0
        rx, rz = -fz, fx
        return (px, py, pz), (fx, fz), (rx, rz)

    def _save_dragged_position(self):
        """仅在玩家握柄拖拽完成时保存键盘位置"""
        if not self.current_transform:
            return
        fr = self._get_hmd_horizontal_frame()
        if not fr:
            return
        (px, py, pz), (fx, fz), (rx, rz) = fr
        t = self.current_transform.m
        cx, cy, cz = t[0][3], t[1][3], t[2][3]
        self.saved_world_pos = (cx, cy, cz)
        self.saved_hmd_pos = (px, py, pz)
        self.saved_hmd_fwd = (fx, fz)

        dx, dy, dz = cx - px, cy - py, cz - pz
        right_off = dx * rx + dz * rz
        fwd_off = dx * fx + dz * fz
        self.saved_rel_offset = (right_off, dy, fwd_off)

    def _restore_dragged_position(self) -> bool:
        """恢复玩家之前拖拽好的键盘位置"""
        if self.saved_world_pos is None or self.saved_rel_offset is None:
            return False
        fr = self._get_hmd_horizontal_frame()
        if not fr:
            return False
        (px, py, pz), (fx, fz), (rx, rz) = fr

        use_exact_world = False
        if self.saved_hmd_pos is not None and self.saved_hmd_fwd is not None:
            hdx = px - self.saved_hmd_pos[0]
            hdy = py - self.saved_hmd_pos[1]
            hdz = pz - self.saved_hmd_pos[2]
            move_dist = math.sqrt(hdx * hdx + hdy * hdy + hdz * hdz)
            dot_fwd = fx * self.saved_hmd_fwd[0] + fz * self.saved_hmd_fwd[1]
            if move_dist < 0.38 and dot_fwd > 0.84:
                use_exact_world = True

        if use_exact_world:
            cx, cy, cz = self.saved_world_pos
        else:
            right_off, dy, fwd_off = self.saved_rel_offset
            cx = px + right_off * rx + fwd_off * fx
            cy = py + dy
            cz = pz + right_off * rz + fwd_off * fz
            self.saved_world_pos = (cx, cy, cz)
            self.saved_hmd_pos = (px, py, pz)
            self.saved_hmd_fwd = (fx, fz)

        mat = self._build_facing_hmd_matrix(cx, cy, cz, (px, py, pz))
        self._set_transform(mat)
        self.last_spawn_hmd_pos = (px, py, pz)
        return True

    def show(self):
        if not self.handle or not self.vr_overlay:
            return False
        if self._restore_dragged_position():
            self.has_user_interacted = True
        else:
            self.reposition_in_front_of_hmd()
            self.has_user_interacted = False

        self.vr_overlay.showOverlay(self.handle)
        self.is_visible = True
        print("[VROverlay] 键盘弹出")
        return True

    def hide(self):
        if not self.handle or not self.vr_overlay:
            return
        self.vr_overlay.hideOverlay(self.handle)
        self._hide_laser_visuals()
        self.is_visible = False
        self.is_dragging = False
        self.drag_controller_idx = None
        self.drag_by_grip = False
        self.is_trigger_down_on_slider = False
        print("[VROverlay] 键盘隐藏")

    def toggle(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def _build_facing_hmd_matrix(self, cx: float, cy: float, cz: float, hmd_pos: Tuple[float, float, float]) -> openvr.HmdMatrix34_t:
        """构建以 (cx, cy, cz) 为中心、且始终水平正对玩家头显眼部的 3x4 变换矩阵"""
        px, py, pz = hmd_pos
        nx = px - cx
        ny = py - cy
        nz = pz - cz
        len_n = math.sqrt(nx * nx + ny * ny + nz * nz)
        if len_n > 0.0001:
            nx /= len_n
            ny /= len_n
            nz /= len_n
        else:
            nx, ny, nz = 0.0, 0.0, 1.0

        rx = nz
        ry = 0.0
        rz = -nx
        len_r = math.sqrt(rx * rx + rz * rz)
        if len_r > 0.0001:
            rx /= len_r
            rz /= len_r
        else:
            rx, ry, rz = 1.0, 0.0, 0.0

        ux_final = ny * rz - nz * ry
        uy_final = nz * rx - nx * rz
        uz_final = nx * ry - ny * rx

        mat = openvr.HmdMatrix34_t()
        mat.m[0][0] = rx;       mat.m[0][1] = ux_final; mat.m[0][2] = nx; mat.m[0][3] = cx
        mat.m[1][0] = ry;       mat.m[1][1] = uy_final; mat.m[1][2] = ny; mat.m[1][3] = cy
        mat.m[2][0] = rz;       mat.m[2][1] = uz_final; mat.m[2][2] = nz; mat.m[2][3] = cz
        return mat

    def reposition_in_front_of_hmd(self):
        """将键盘精确定位在头显水平正前方偏下方、距离 0.56 米的舒适区"""
        fr = self._get_hmd_horizontal_frame()
        if not fr:
            return
        (px, py, pz), (fx, fz), _ = fr

        cfg_overlay = config.get("overlay", default={}) or {}
        dist = float(cfg_overlay.get("distance_m", 0.56))
        pitch_deg = float(cfg_overlay.get("pitch_deg", -22.0))

        pitch_rad = math.radians(abs(pitch_deg))
        down_offset = dist * math.sin(pitch_rad)
        fwd_offset = dist * math.cos(pitch_rad)

        cx = px + fx * fwd_offset
        cy = py - down_offset
        cz = pz + fz * fwd_offset

        mat = self._build_facing_hmd_matrix(cx, cy, cz, (px, py, pz))
        self._set_transform(mat)
        self.last_spawn_hmd_pos = (px, py, pz)

    def _resolve_valid_controller(self, controller_idx: Optional[int]) -> Optional[int]:
        """确保返回有效的手柄设备索引"""
        if not self.vr_system:
            return None
        if (
            controller_idx is not None
            and 1 <= controller_idx < openvr.k_unMaxTrackedDeviceCount
            and self.vr_system.isTrackedDeviceConnected(controller_idx)
            and self.vr_system.getTrackedDeviceClass(controller_idx) == openvr.TrackedDeviceClass_Controller
        ):
            return controller_idx

        fallback = None
        for idx in range(1, openvr.k_unMaxTrackedDeviceCount):
            if self.vr_system.isTrackedDeviceConnected(idx) and self.vr_system.getTrackedDeviceClass(idx) == openvr.TrackedDeviceClass_Controller:
                if self.vr_system.getControllerRoleForTrackedDeviceIndex(idx) == openvr.TrackedControllerRole_RightHand:
                    return idx
                if fallback is None:
                    fallback = idx
        return fallback

    def start_drag(self, controller_idx: Optional[int] = None, poses=None, by_grip: bool = False):
        """开始跟随手柄在 3D 空间平移键盘"""
        if not self.vr_system or not self.current_transform:
            return
        valid_idx = self._resolve_valid_controller(controller_idx)
        if valid_idx is None:
            return

        if poses is None:
            poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
            poses = poses_t()
            self.vr_system.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0.0, poses)

        if poses[valid_idx].bPoseIsValid:
            cm = poses[valid_idx].mDeviceToAbsoluteTracking
            self.drag_start_ctrl_pos = (cm[0][3], cm[1][3], cm[2][3])
            self.drag_start_panel_pos = (
                self.current_transform.m[0][3],
                self.current_transform.m[1][3],
                self.current_transform.m[2][3],
            )
            self.is_dragging = True
            self.drag_controller_idx = valid_idx
            self.drag_by_grip = by_grip
            self.drag_start_time = time.time()
            self.has_user_interacted = True
            self._hide_laser_visuals()
            self.trigger_haptic(valid_idx, 1800)

    def stop_drag(self):
        if self.is_dragging:
            self._save_dragged_position()
        self.is_dragging = False
        self.drag_controller_idx = None
        self.drag_by_grip = False

    def trigger_haptic(self, controller_idx: int, duration_us: int = 1800):
        if self.vr_system and controller_idx is not None and controller_idx > 0:
            try:
                self.vr_system.triggerHapticPulse(controller_idx, 0, duration_us)
            except Exception:
                pass

    def _compute_ray_from_controller(self, cm) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """从手柄位姿矩阵计算符合人体工学瞄准的角度射线 (下倾约 32°，适配 Quest/Pico/VD)"""
        ox, oy, oz = cm[0][3], cm[1][3], cm[2][3]
        fz_x, fz_y, fz_z = -cm[0][2], -cm[1][2], -cm[2][2]
        fy_x, fy_y, fy_z = -cm[0][1], -cm[1][1], -cm[2][1]

        # 稍微沿握持方向向前 3cm 出射，避免挡住手模
        angle_rad = math.radians(32.0)
        ca, sa = math.cos(angle_rad), math.sin(angle_rad)
        dx = fz_x * ca + fy_x * sa
        dy = fz_y * ca + fy_y * sa
        dz = fz_z * ca + fy_z * sa
        dl = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        dx, dy, dz = dx / dl, dy / dl, dz / dl
        return (ox + dx * 0.03, oy + dy * 0.03, oz + dz * 0.03), (dx, dy, dz)

    def _raycast_keyboard(
        self, ray_origin: Tuple[float, float, float], ray_dir: Tuple[float, float, float]
    ) -> Optional[Tuple[float, float, Tuple[float, float, float], float]]:
        """
        精确计算手柄射线与当前 3D 键盘平面的交点。
        返回: (u, v, hit_point_3d, distance)，其中 u, v 在 [0, 1] 范围内表示命中键盘内部。
        完全独立于 SteamVR 焦点系统，因此即使在 VD 串流下也 100% 精准可靠！
        """
        if not self.current_transform:
            return None
        m = self.current_transform
        cx, cy, cz = m[0][3], m[1][3], m[2][3]
        rx, ry, rz = m[0][0], m[1][0], m[2][0]
        ux, uy, uz = m[0][1], m[1][1], m[2][1]
        nx, ny, nz = m[0][2], m[1][2], m[2][2]

        ox, oy, oz = ray_origin
        dx, dy, dz = ray_dir

        # 射线方向与法线的点积
        denom = dx * nx + dy * ny + dz * nz
        if denom >= -0.04:  # 背面或平行掠过，不响应
            return None

        t = ((cx - ox) * nx + (cy - oy) * ny + (cz - oz) * nz) / denom
        if t < 0.04 or t > 3.8:
            return None

        hx = ox + dx * t
        hy = oy + dy * t
        hz = oz + dz * t

        vx, vy, vz = hx - cx, hy - cy, hz - cz
        lx = vx * rx + vy * ry + vz * rz
        ly = vx * ux + vy * uy + vz * uz

        w_m = self.width_m
        h_m = w_m * (560.0 / 1000.0)

        u = (lx / w_m) + 0.5
        v = 0.5 - (ly / h_m)

        if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0:
            return u, v, (hx, hy, hz), t
        return None

    def _detect_virtual_desktop(self) -> bool:
        """
        智能检测当前 VR 运行时是否为 Virtual Desktop 串流。
        1. 检查 HMD (设备 0) 的驱动与厂商属性是否包含 'virtualdesktop'。
        2. 检查控制器 (设备 1..64) 的驱动与厂商属性。
        3. 若 HMD 为原生 'lighthouse' (Index/Vive)，则判定为原生 SteamVR，绝不出双线。
        4. 兜底检查 Windows 是否正在运行 VirtualDesktop.Streamer.exe。
        """
        if not self.vr_system:
            return False
        # 1. 检查 HMD (设备 0)
        for prop in (
            openvr.Prop_TrackingSystemName_String,
            openvr.Prop_ManufacturerName_String,
            openvr.Prop_ModelNumber_String,
            openvr.Prop_RegisteredDeviceType_String,
        ):
            try:
                val = self.vr_system.getStringTrackedDeviceProperty(openvr.k_unTrackedDeviceIndex_Hmd, prop)
                if val and "virtualdesktop" in val.lower():
                    return True
            except Exception:
                pass

        # 2. 检查所有连接的追踪控制器
        for dev_idx in range(1, openvr.k_unMaxTrackedDeviceCount):
            if not self.vr_system.isTrackedDeviceConnected(dev_idx):
                continue
            for prop in (
                openvr.Prop_TrackingSystemName_String,
                openvr.Prop_ManufacturerName_String,
                openvr.Prop_ModelNumber_String,
            ):
                try:
                    val = self.vr_system.getStringTrackedDeviceProperty(dev_idx, prop)
                    if val and "virtualdesktop" in val.lower():
                        return True
                except Exception:
                    pass

        # 3. 若 HMD 系统明确是 lighthouse (Valve Index / HTC Vive)，绝不属于 VD
        try:
            hmd_sys = self.vr_system.getStringTrackedDeviceProperty(
                openvr.k_unTrackedDeviceIndex_Hmd, openvr.Prop_TrackingSystemName_String
            )
            if hmd_sys and "lighthouse" in hmd_sys.lower():
                return False
        except Exception:
            pass

        return self._is_vd_process_running()

    def _is_vd_process_running(self) -> bool:
        """检查系统进程列表中是否有活跃的 VirtualDesktop.Streamer.exe"""
        try:
            k32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002
            hSnapshot = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            found = False
            if k32.Process32FirstW(hSnapshot, ctypes.byref(pe)):
                while True:
                    if "virtualdesktop.streamer" in pe.szExeFile.lower():
                        found = True
                        break
                    if not k32.Process32NextW(hSnapshot, ctypes.byref(pe)):
                        break
            k32.CloseHandle(hSnapshot)
            return found
        except Exception:
            return False

    def _is_in_vr_scene(self) -> bool:
        """检测当前是否处于 VRChat 等 VR 游戏场景中（且未打开 SteamVR 系统面板）"""
        now = time.time()
        if now - self._last_scene_check_ts >= 0.5:
            self._last_scene_check_ts = now
            try:
                if self._vr_apps is None:
                    self._vr_apps = openvr.VRApplications()
                scene_pid = self._vr_apps.getCurrentSceneProcessId()
                dash_open = bool(self.vr_overlay and self.vr_overlay.isDashboardVisible())
                self._cached_in_scene = (scene_pid > 0) and (not dash_open)
            except Exception:
                self._cached_in_scene = True
        return self._cached_in_scene

    def _should_render_laser_guide(self) -> bool:
        """根据当前配置模式判断是否渲染 3D 激光引导线与准星"""
        if self.laser_mode == "off":
            return False
        if self.laser_mode == "on":
            return True
        # "auto" 模式：仅在 VD 串流且已进入 VRChat 等场景（非 SteamVR 外面大厅/面板）时渲染，避免双线抢控制权
        return bool(self.is_vd_active) and self._is_in_vr_scene()

    def set_laser_mode(self, mode: str):
        self.laser_mode = mode
        if not self._should_render_laser_guide():
            self._hide_laser_visuals()

    def _update_laser_visuals(
        self,
        ray_origin: Tuple[float, float, float],
        hit_point: Tuple[float, float, float],
        hmd_pos: Tuple[float, float, float],
    ):
        """
        在 3D VR 空间中实时绘制从手柄射向键盘的青蓝色发光激光线以及键盘表面的发光准星。
        无论使用 VD、Quest Link、AirLink 还是 Pico 串流，都能始终看到清晰流畅的引导线！
        """
        if not self.vr_overlay:
            return

        ox, oy, oz = ray_origin
        hx, hy, hz = hit_point
        vx, vy, vz = hx - ox, hy - oy, hz - oz
        length = math.sqrt(vx * vx + vy * vy + vz * vz)
        if length < 0.02:
            return

        # 状态机：仅在从隐藏切换为可见时向 SteamVR 发送一次 showOverlay
        if not self.is_laser_visible:
            if self.laser_handle:
                try:
                    self.vr_overlay.showOverlay(self.laser_handle)
                except Exception:
                    pass
            if self.cursor_handle:
                try:
                    self.vr_overlay.showOverlay(self.cursor_handle)
                except Exception:
                    pass
            self.is_laser_visible = True

        # 1. 绘制 3D 激光光束 (两点连线，始终朝向玩家视线)
        if self.laser_handle:
            mx, my, mz = (ox + hx) * 0.5, (oy + hy) * 0.5, (oz + hz) * 0.5
            xx, xy, xz = vx / length, vy / length, vz / length
            ex, ey, ez = hmd_pos[0] - mx, hmd_pos[1] - my, hmd_pos[2] - mz
            yx = ey * xz - ez * xy
            yy = ez * xx - ex * xz
            yz = ex * xy - ey * xx
            yl = math.sqrt(yx * yx + yy * yy + yz * yz)
            if yl > 0.0001:
                yx /= yl
                yy /= yl
                yz /= yl
            else:
                yx, yy, yz = 0.0, 1.0, 0.0
            zx = xy * yz - xz * yy
            zy = xz * yx - xx * yz
            zz = xx * yy - xy * yx

            lmat = openvr.HmdMatrix34_t()
            lmat.m[0][0] = xx; lmat.m[0][1] = yx; lmat.m[0][2] = zx; lmat.m[0][3] = mx
            lmat.m[1][0] = xy; lmat.m[1][1] = yy; lmat.m[1][2] = zy; lmat.m[1][3] = my
            lmat.m[2][0] = xz; lmat.m[2][1] = yz; lmat.m[2][2] = zz; lmat.m[2][3] = mz

            if abs(length - self.last_laser_length) > 0.003:
                self.vr_overlay.setOverlayWidthInMeters(self.laser_handle, length)
                try:
                    # 保持光束粗细约为 3.2mm
                    aspect = (length / 0.0032) * (16.0 / 128.0)
                    self.vr_overlay.setOverlayTexelAspect(self.laser_handle, aspect)
                except Exception:
                    pass
                self.last_laser_length = length

            self.vr_overlay.setOverlayTransformAbsolute(self.laser_handle, openvr.TrackingUniverseStanding, lmat)

        # 2. 绘制键盘按键上的发光圆环准星
        if self.cursor_handle and self.current_transform:
            m = self.current_transform
            nx, ny, nz = m[0][2], m[1][2], m[2][2]
            cmat = openvr.HmdMatrix34_t()
            for r in range(3):
                for c in range(3):
                    cmat.m[r][c] = m.m[r][c]
            # 准星稍微悬浮在键盘表面 1.5mm 防止 Z-fighting
            cmat.m[0][3] = hx + nx * 0.0015
            cmat.m[1][3] = hy + ny * 0.0015
            cmat.m[2][3] = hz + nz * 0.0015
            self.vr_overlay.setOverlayTransformAbsolute(self.cursor_handle, openvr.TrackingUniverseStanding, cmat)

    def _hide_laser_visuals(self):
        """隐藏激光光束与发光准星 (状态机防护：仅在当前可见时向 SteamVR 发送一次隐藏指令)"""
        if not self.is_laser_visible:
            return
        if self.vr_overlay:
            if self.laser_handle:
                try:
                    self.vr_overlay.hideOverlay(self.laser_handle)
                except Exception:
                    pass
            if self.cursor_handle:
                try:
                    self.vr_overlay.hideOverlay(self.cursor_handle)
                except Exception:
                    pass
        self.is_laser_visible = False
        self.last_laser_length = 0.0

    def step_vr_interaction(self) -> List[Tuple[str, int, int, int]]:
        """
        每帧执行一次 VR 交互轮询：
        1. 右手柄摇杆严格双击呼出/收起。
        2. 握柄键 (Grip) 专属于拖拽键盘，严格由侧面握柄触发，B 键/A 键绝对不触发拖动！
        3. 自带 3D 激光光束与键盘瞄准准星，VD 串流也能完美瞄准！
        4. 零焦点夺取：VRChat 角色永远处于活跃状态，永不进 AFK，摇杆自由走路绝不受限！
        """
        ui_events: List[Tuple[str, int, int, int]] = []
        if not self.vr_system or not self.vr_overlay:
            return ui_events

        now_t = time.time()

        # 1. 获取所有追踪设备位姿
        poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
        poses = poses_t()
        self.vr_system.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0.0, poses)

        hmd_pose = poses[openvr.k_unTrackedDeviceIndex_Hmd]
        hmd_pos = (0.0, 1.6, 0.0)
        if hmd_pose.bPoseIsValid:
            hm = hmd_pose.mDeviceToAbsoluteTracking
            hmd_pos = (hm[0][3], hm[1][3], hm[2][3])

            if self.is_visible and not self.has_user_interacted and self.saved_world_pos is None and self.last_spawn_hmd_pos is not None:
                dx = hmd_pos[0] - self.last_spawn_hmd_pos[0]
                dy = hmd_pos[1] - self.last_spawn_hmd_pos[1]
                dz = hmd_pos[2] - self.last_spawn_hmd_pos[2]
                if math.sqrt(dx * dx + dy * dy + dz * dz) > 0.65:
                    self.reposition_in_front_of_hmd()

        # 2. 清空 SteamVR 系统事件队列
        ev = openvr.VREvent_t()
        while self.vr_system.pollNextEvent(ev):
            if ev.eventType == openvr.VREvent_Quit:
                print("[VROverlay] 检测到 SteamVR 已退出，安全结束键盘进程。")
                sys.exit(0)

        # 3. 轮询手柄按键与交互
        cfg_hotkey = config.get("hotkey", default={}) or {}
        target_role_str = cfg_hotkey.get("controller", "right")
        target_role = (
            openvr.TrackedControllerRole_LeftHand
            if target_role_str == "left"
            else openvr.TrackedControllerRole_RightHand
        )
        interval_sec = float(cfg_hotkey.get("double_click_interval_ms", 420)) / 1000.0

        any_grip_now = False
        hit_candidate = None

        for dev_idx in range(1, openvr.k_unMaxTrackedDeviceCount):
            if not self.vr_system.isTrackedDeviceConnected(dev_idx):
                continue
            if self.vr_system.getTrackedDeviceClass(dev_idx) != openvr.TrackedDeviceClass_Controller:
                continue

            role = self.vr_system.getControllerRoleForTrackedDeviceIndex(dev_idx)
            ok, state = self.vr_system.getControllerState(dev_idx)
            if state is None:
                continue

            btn_mask = state.ulButtonPressed

            # --- A. 严格双击摇杆检测 (呼出/隐藏键盘) ---
            if role == target_role:
                thumb_now = bool(btn_mask & ((1 << openvr.k_EButton_Axis0) | (1 << 35)))
                thumb_prev = self.prev_thumbstick_pressed.get(dev_idx, False)
                self.prev_thumbstick_pressed[dev_idx] = thumb_now

                first_t = self.thumb_first_press_time.get(dev_idx, 0.0)
                released_between = self.thumb_released_after_first.get(dev_idx, False)

                if thumb_now and not thumb_prev:
                    if released_between and 0.04 <= (now_t - first_t) <= interval_sec:
                        self.toggle()
                        self.trigger_haptic(dev_idx, 2600)
                        self.thumb_first_press_time[dev_idx] = 0.0
                        self.thumb_released_after_first[dev_idx] = False
                    else:
                        self.thumb_first_press_time[dev_idx] = now_t
                        self.thumb_released_after_first[dev_idx] = False
                elif not thumb_now and thumb_prev:
                    if (now_t - first_t) <= interval_sec:
                        self.thumb_released_after_first[dev_idx] = True
                    else:
                        self.thumb_released_after_first[dev_idx] = False

            # --- B. 握柄键 (Grip) 检测：严格读取中指侧面握柄轴 rAxis[2].x ---
            analog_grip = state.rAxis[2].x
            digital_grip = bool(btn_mask & ((1 << 2) | (1 << 34)))
            grip_prev = self.prev_grip_pressed.get(dev_idx, False)
            if grip_prev:
                grip_now = (analog_grip > 0.30) or digital_grip
            else:
                grip_now = (analog_grip > 0.50) or digital_grip
            self.prev_grip_pressed[dev_idx] = grip_now

            if grip_now:
                any_grip_now = True

            # --- C. 食指扳机键 (Trigger) 与 3D 射线瞄准 ---
            if self.is_visible and poses[dev_idx].bPoseIsValid:
                cm = poses[dev_idx].mDeviceToAbsoluteTracking
                ray_origin, ray_dir = self._compute_ray_from_controller(cm)
                hit_res = self._raycast_keyboard(ray_origin, ray_dir)

                # 握柄拖拽：按下握柄键直接启动平移
                if grip_now and not grip_prev and not self.is_dragging:
                    self.start_drag(dev_idx, poses, by_grip=True)

                # 食指扳机检测 (打字点击)
                analog_trig = state.rAxis[1].x
                digital_trig = bool(btn_mask & (1 << 33))
                trig_now = (analog_trig > 0.58) or digital_trig
                trig_prev = self.prev_trigger_pressed.get(dev_idx, False)
                self.prev_trigger_pressed[dev_idx] = trig_now

                if hit_res is not None and not self.is_dragging:
                    u, v, hit_pt, dist = hit_res
                    px = int(max(0, min(1000, u * 1000.0)))
                    py = int(max(0, min(560, v * 560.0)))

                    # 记录活跃命中手柄，用于渲染 3D 激光线
                    if hit_candidate is None or role == target_role:
                        hit_candidate = (ray_origin, hit_pt, px, py, dev_idx)

                    self.last_hover_xy = (px, py)
                    if trig_now and not trig_prev:
                        self.has_user_interacted = True
                        self.is_trigger_down_on_slider = True
                        ui_events.append(("click", px, py, dev_idx))
                        self.trigger_haptic(dev_idx, 1600)
                    elif trig_now and trig_prev and self.is_trigger_down_on_slider:
                        ui_events.append(("drag_hold", px, py, dev_idx))
                    elif not trig_now and trig_prev:
                        self.is_trigger_down_on_slider = False

        # --- D. 更新或隐藏 3D 激光引导光束与表面发光准星 ---
        if self.is_visible and not self.is_dragging and hit_candidate is not None:
            self.current_hover_xy = (hit_candidate[2], hit_candidate[3])
        else:
            self.current_hover_xy = None

        should_render_laser = self._should_render_laser_guide()
        if self.is_visible and not self.is_dragging and hit_candidate is not None and should_render_laser:
            r_orig, h_pt, px, py, dev_idx = hit_candidate
            self._update_laser_visuals(r_orig, h_pt, hmd_pos)
        else:
            self._hide_laser_visuals()

        # 松开握柄键时停止拖拽
        if self.is_dragging and self.drag_by_grip and not any_grip_now:
            self.stop_drag()

        # 更新拖拽中的位姿
        if self.is_visible and self.is_dragging and self.drag_controller_idx is not None:
            d_idx = self.drag_controller_idx
            if 1 <= d_idx < openvr.k_unMaxTrackedDeviceCount and poses[d_idx].bPoseIsValid and self.current_transform:
                cm = poses[d_idx].mDeviceToAbsoluteTracking
                dx = cm[0][3] - self.drag_start_ctrl_pos[0]
                dy = cm[1][3] - self.drag_start_ctrl_pos[1]
                dz = cm[2][3] - self.drag_start_ctrl_pos[2]
                ncx = self.drag_start_panel_pos[0] + dx
                ncy = self.drag_start_panel_pos[1] + dy
                ncz = self.drag_start_panel_pos[2] + dz
                mat = self._build_facing_hmd_matrix(ncx, ncy, ncz, hmd_pos)
                self._set_transform(mat)

        self.is_any_grip_pressed = any_grip_now
        return ui_events

    def upload_texture(self, img_bytes: bytes, width: int = 1000, height: int = 560):
        """GPU 硬件加速原生显存零闪烁渲染 (彻底告别单帧黑屏闪烁与 IPC 队列拥堵)"""
        if not self.handle or not self.vr_overlay:
            return
        if self.gl_ctx and self.gl_ctx.is_valid and self.ovr_texture:
            try:
                tid = self.gl_ctx.update_texture(img_bytes, width, height)
                if tid:
                    self.ovr_texture.handle = ctypes.c_void_p(tid)
                    self.vr_overlay.setOverlayTexture(self.handle, self.ovr_texture)
                    return
            except Exception as e:
                print(f"[VROverlay] GPU 显存纹理提交异常 ({type(e).__name__}): {repr(e)}")

        # 安全回退方案
        try:
            c_buf = (ctypes.c_char * len(img_bytes)).from_buffer_copy(img_bytes)
            self._c_buf = c_buf
            self.vr_overlay.setOverlayRaw(self.handle, c_buf, width, height, 4)
        except Exception as e:
            print(f"[VROverlay] 贴图上传失败 ({type(e).__name__}): {repr(e)}")

    def set_hud_pose(self, anchor: str = "hmd", width_m: float = 0.48, distance_m: float = 1.25, y_offset_m: float = -0.18):
        """设置语音翻译 HUD 挂载设备（头显 HMD / 左手 / 右手）及大小远近"""
        if not self.hud_handle or not self.vr_overlay or not self.vr_system:
            return
        try:
            target_idx = openvr.k_unTrackedDeviceIndex_Hmd
            eff_width = max(0.20, min(1.0, float(width_m)))
            mat = openvr.HmdMatrix34_t()

            if anchor in ("left", "right"):
                role = (
                    openvr.TrackedControllerRole_LeftHand
                    if anchor == "left"
                    else openvr.TrackedControllerRole_RightHand
                )
                ctrl_idx = self.vr_system.getTrackedDeviceIndexForControllerRole(role)
                if ctrl_idx != openvr.k_unTrackedDeviceIndexInvalid:
                    target_idx = ctrl_idx
                    eff_width = max(0.14, min(0.55, eff_width * 0.55))
                    pitch = math.radians(-28.0)
                    cp, sp = math.cos(pitch), math.sin(pitch)
                    dist_hand = 0.08 + max(0.0, float(distance_m) - 0.5) * 0.16
                    y_hand = 0.12 + float(y_offset_m) * 0.25
                    mat.m[0][0], mat.m[0][1], mat.m[0][2], mat.m[0][3] = 1.0, 0.0, 0.0, 0.0
                    mat.m[1][0], mat.m[1][1], mat.m[1][2], mat.m[1][3] = 0.0, cp, -sp, y_hand
                    mat.m[2][0], mat.m[2][1], mat.m[2][2], mat.m[2][3] = 0.0, sp, cp, -dist_hand
                    self.vr_overlay.setOverlayWidthInMeters(self.hud_handle, eff_width)
                    self.vr_overlay.setOverlayTransformTrackedDeviceRelative(self.hud_handle, target_idx, mat)
                    return

            # 默认头显 HUD 随动
            pitch = math.radians(max(-15.0, min(15.0, float(y_offset_m) * -22.0)))
            cp, sp = math.cos(pitch), math.sin(pitch)
            mat.m[0][0], mat.m[0][1], mat.m[0][2], mat.m[0][3] = 1.0, 0.0, 0.0, 0.0
            mat.m[1][0], mat.m[1][1], mat.m[1][2], mat.m[1][3] = 0.0, cp, -sp, float(y_offset_m)
            mat.m[2][0], mat.m[2][1], mat.m[2][2], mat.m[2][3] = 0.0, sp, cp, -max(0.45, min(2.5, float(distance_m)))
            self.vr_overlay.setOverlayWidthInMeters(self.hud_handle, eff_width)
            self.vr_overlay.setOverlayTransformTrackedDeviceRelative(self.hud_handle, target_idx, mat)
        except Exception as e:
            print(f"[VROverlay] 设置 HUD 位姿失败: {e}")

    def show_hud(self):
        if self.hud_handle and self.vr_overlay and not self.hud_visible:
            try:
                self.vr_overlay.showOverlay(self.hud_handle)
                self.hud_visible = True
            except Exception:
                pass

    def hide_hud(self):
        if self.hud_handle and self.vr_overlay and self.hud_visible:
            try:
                self.vr_overlay.hideOverlay(self.hud_handle)
                self.hud_visible = False
            except Exception:
                pass

    def upload_hud_texture(self, img_bytes: bytes, width: int = 800, height: int = 180):
        if not self.hud_handle or not self.vr_overlay:
            return
        if self.hud_gl_ctx and self.hud_gl_ctx.is_valid and self.hud_ovr_texture:
            try:
                tid = self.hud_gl_ctx.update_texture(img_bytes, width, height)
                if tid:
                    self.hud_ovr_texture.handle = ctypes.c_void_p(tid)
                    self.vr_overlay.setOverlayTexture(self.hud_handle, self.hud_ovr_texture)
                    return
            except Exception:
                pass
        try:
            c_buf = (ctypes.c_char * len(img_bytes)).from_buffer_copy(img_bytes)
            self._hud_c_buf = c_buf
            self.vr_overlay.setOverlayRaw(self.hud_handle, c_buf, width, height, 4)
        except Exception as e:
            print(f"[VROverlay] HUD 贴图上传失败: {e}")

    def shutdown(self):
        """主动销毁所有 Overlay、OpenGL 上下文并关闭 OpenVR，释放 DLL 锁"""
        try:
            if self.vr_overlay:
                for h in (self.handle, self.laser_handle, self.cursor_handle, self.hud_handle):
                    if h:
                        try:
                            self.vr_overlay.hideOverlay(h)
                            self.vr_overlay.destroyOverlay(h)
                        except Exception:
                            pass
            self.handle = None
            self.laser_handle = None
            self.cursor_handle = None
            self.hud_handle = None
            if self.gl_ctx:
                self.gl_ctx.destroy()
                self.gl_ctx = None
            if self.hud_gl_ctx:
                self.hud_gl_ctx.destroy()
                self.hud_gl_ctx = None
            if self.vr_system is not None:
                openvr.shutdown()
                self.vr_system = None
                self.vr_overlay = None
        except Exception as e:
            print(f"[VROverlay] 退出清理提示: {e}")
