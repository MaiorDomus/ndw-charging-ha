"""Constants for the NDW Charging Point integration."""

DOMAIN = "ndw_charging"

# National Access Point (NDW) open data feed. Free, no API key, no rate limit.
# All Dutch public charge point operators (Allego included) are legally required
# (EU AFIR) to publish live OCPI status here. ~18MB gzipped / ~200MB decompressed
# for the whole country.
DATA_URL = "https://opendata.ndw.nu/charging_point_locations_ocpi.json.gz"

CONF_LOCATION_ID = "location_id"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 600  # seconds
MIN_UPDATE_INTERVAL = 120  # seconds - be a reasonable citizen of a free public feed

REQUEST_TIMEOUT = 120  # seconds - the file is large, give it room
