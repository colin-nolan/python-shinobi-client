from dataclasses import dataclass




@dataclass
class Shinobi:
    """
    Model of Shinobi installation.
    """
    host: str
    port: str
    super_user_token: str
    super_user_email: str = None
    super_user_password: str = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def user(self) -> "ShinobiUserOrm":
        from shinobi_client import ShinobiUserOrm
        return ShinobiUserOrm(self)
