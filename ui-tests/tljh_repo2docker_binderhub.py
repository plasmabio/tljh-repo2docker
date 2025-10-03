c.TljhRepo2Docker.db_url = "sqlite:///tljh_repo2docker.sqlite"

c.TljhRepo2Docker.machine_profiles = [
    {"label": "Small", "cpu": 2, "memory": 2},
    {"label": "Medium", "cpu": 4, "memory": 4},
    {"label": "Large", "cpu": 8, "memory": 8},
]

c.TljhRepo2Docker.node_selector = {
    "gpu": {"description": "GPU description", "values": ["yes", "no"]},
    "ssd": {"description": "SSD description", "values": ["yes", "no"]},
}

c.TljhRepo2Docker.binderhub_url = "http://localhost:8585/services/binder/"

c.TljhRepo2Docker.logo_url = "/custom/logo/url"
