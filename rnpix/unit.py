"""unit testing

:copyright: Copyright (c) 2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def image_create(path_dt):
    from rnpix import common, unit

    return path_dt.new(
        purebasename=common.exif_set(
            image_create_handle(path_dt.purebasename),
            path=path_dt,
            date_time=common.date_time_parse(path_dt),
            description=path_dt.purebasename,
        ).strftime(common.BASE_FTIME)
    )


def image_create_handle(text="anything"):
    from PIL import Image, ImageFont, ImageDraw
    import io

    with Image.new("RGB", (500, 300), color=(255, 255, 200)) as i:
        ImageDraw.Draw(i).text(
            (100, 100), text, fill=(0, 0, 0), font=ImageFont.load_default()
        )
        b = io.BytesIO()
        i.save(b, "JPEG")
    b.seek(0)
    return b
