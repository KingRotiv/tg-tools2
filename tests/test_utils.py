import os
import tempfile

import pytest
from PIL import Image

from tg_tools.exceptions import TGToolsError
from tg_tools.utils import (
    THUMBNAIL_MAX_HEIGHT,
    THUMBNAIL_MAX_WIDTH,
    file_thumbnail_to_base64,
    format_size,
)


@pytest.mark.parametrize(
    "size,expected",
    [
        (500, "500.00 B"),
        (2048, "2.00 KB"),
        (1048576, "1.00 MB"),
        (1073741824, "1.00 GB"),
        (1099511627776, "1.00 TB"),
    ],
)
def test_format_size(size, expected):
    """
    Testa se a função format_size retorna o tamanho formatado corretamente para diferentes valores de bytes.
    """
    assert format_size(size) == expected


# Teste para file_thumbnail_to_base64 exige arquivos de imagem reais e manipulação de arquivos,
def create_temp_image(width=100, height=100):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        img = Image.new("RGB", (width, height), color="red")
        img.save(tmp.name, format="JPEG")
        return tmp.name


def test_file_thumbnail_to_base64_valid():
    """
    Testa se uma imagem válida é convertida para base64 corretamente.
    """
    img_path = create_temp_image()
    result = file_thumbnail_to_base64(img_path)
    assert isinstance(result, str)
    assert len(result) > 0


# Teste de imagem com dimensões inválidas
def test_file_thumbnail_to_base64_invalid_dimensions():
    """
    Testa se uma imagem com dimensões inválidas dispara um erro (TGToolsError), conforme esperado pela função.
    """
    img_path = create_temp_image(
        width=THUMBNAIL_MAX_WIDTH + 1, height=THUMBNAIL_MAX_HEIGHT + 1
    )
    with pytest.raises(TGToolsError):
        file_thumbnail_to_base64(img_path)
    os.remove(img_path)
