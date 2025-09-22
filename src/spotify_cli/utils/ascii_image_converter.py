from io import BytesIO

from PIL import Image
from ascii_magic import AsciiArt
from requests import get


def get_ascii_of_image(image_url: str, height: int, width_ratio: float | int) -> str:
    resp = get(image_url)
    resp.raise_for_status()

    pill_image = Image.open(BytesIO(resp.content))
    pill_image.load()
    img = AsciiArt.from_pillow_image(pill_image)
    return img.to_ascii(
        columns=height,
        width_ratio=width_ratio
    )


if __name__ == "__main__":
    url = "https://i.scdn.co/image/ab67616d00001e026ab9aff73fa181d27dd8b9e0"

    response = get(url, stream=True)
    response.raise_for_status()

    _image = Image.open(BytesIO(response.content))
    _image.load()
    image = AsciiArt.from_pillow_image(_image)
    output = image.to_terminal(
        columns=100,
        width_ratio=90
    )
    print("a")