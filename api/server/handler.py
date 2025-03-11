from mangum import Mangum
from .main import app
import os

# Configure Mangum handler for AWS Lambda container
handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path=os.getenv("API_GATEWAY_BASE_PATH", "/"),
    strip_stage_path=True
) 