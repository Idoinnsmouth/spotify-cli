from io import BytesIO

from PIL import Image
from requests import get
from rich_pixels import Pixels


def get_image_from_url(image_url: str, size: tuple[int, int]) -> Pixels:
    resp = get(image_url)
    resp.raise_for_status()

    pill_image = Image.open(BytesIO(resp.content))
    return Pixels.from_image(pill_image, resize=size)