"""Methods to load and manage images."""
from typing import Iterable
from PIL import Image

def generate_thumbnails(
        filepaths: Iterable[str],
        max_size: tuple[float, float] | None = None
        ) -> dict[str, Image.Image]:
    """
    Loads images from a iterable of file paths and generates thumbnails.

    Parameters
    ----------
    filepaths: Iterable[str], required
        Paths to image files.
    max_size: tuple[float, float], optional, default (100, 100)
        Maximum thumbnail size (width, height).
    
    Returns
    -------
    dict[str, Image]
        Dictionary with filepaths as keys and thumbnails as values.
    """
    if max_size is None:
        max_size = (100, 100)
    thumbnails: dict[str, Image.Image] = {}
    for f in filepaths:
        thumbnails[f] = Image.open(f)
        thumbnails[f].thumbnail(max_size)
    return thumbnails

class ImageManager:
    def __init__(self):
        self.filepaths: list[str] = None
        self.images: dict[str, Image.Image] = None
    
    def set_filepaths(
            self,
            filepaths: Iterable[str]
        ) -> None:
        self.filepaths = list(filepaths)
        self.images = {}
        for f in self.filepaths:
            key = f.rsplit("/", maxsplit=1)[-1]
            self.images[key] = Image.open(f)
