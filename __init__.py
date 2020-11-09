from python_graphql_client import GraphqlClient

from .const import BASE_URL


PLATFORMS = ["sensor"]


graph_client = GraphqlClient(endpoint=BASE_URL)


def base_unique_id(gtfs_id, route=None):
    """Return unique id for entries in configuration."""
    if route is None or route.lower() == "all"
    	return f"{gtfs_id} all"
    else:
    	return f"{gtfs_id} {route}"
