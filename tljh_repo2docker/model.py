from dataclasses import dataclass, fields


@dataclass
class UserModel:

    name: str
    admin: bool
    servers: dict
    roles: list

    @classmethod
    def from_dict(self, kwargs_dict: dict):
        field_names = set(f.name for f in fields(UserModel))
        new_kwargs = {k: v for k, v in kwargs_dict.items() if k in field_names}
        return UserModel(**new_kwargs)

    def all_spawners(self) -> list:
        sp = []
        for server in self.servers.values():
            active = bool(server.get("pending", None) or server.get("ready", False))
            if active or len(server["name"]) > 0:
                sp.append(
                    {
                        "name": server.get("name", ""),
                        "url": server.get("url", ""),
                        "last_activity": server.get("last_activity", None),
                        "active": active,
                        "user_options": server.get("user_options", None),
                    }
                )
        return sp
