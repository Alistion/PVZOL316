# services/Auth.py
import os


class AuthService:
    @staticmethod
    def process_avatar_upload(uid, avatar_file):
        """处理头像上传逻辑，返回可访问的 URL 路径"""
        if not avatar_file or not avatar_file.filename:
            return "/pvz/avatar/1.png"

        save_dir = os.path.join("cache", "pvz", "avatar")
        os.makedirs(save_dir, exist_ok=True)

        ext = avatar_file.filename.rsplit(".", 1)[-1]
        filename = f"{uid}.{ext}"
        avatar_file.save(os.path.join(save_dir, filename))

        return f"/pvz/avatar/{filename}"
