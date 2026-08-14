import extra_streamlit_components as stx

class EncryptedCookiesManager:
    def __init__(self, prefix, password):
        self.cookie_manager = stx.CookieManager()
        self.prefix = prefix
        self.password = password

    def ready(self):
        return True

    def get(self, key, default=None):
        return self.cookie_manager.get(f"{self.prefix}_{key}") or default

    def __setitem__(self, key, value):
        self.cookie_manager.set(f"{self.prefix}_{key}", value)

    def __getitem__(self, key):
        return self.cookie_manager.get(f"{self.prefix}_{key}")

    def __contains__(self, key):
        return self.cookie_manager.get(f"{self.prefix}_{key}") is not None

    def __delitem__(self, key):
        self.cookie_manager.delete(f"{self.prefix}_{key}")

    def save(self):
        pass