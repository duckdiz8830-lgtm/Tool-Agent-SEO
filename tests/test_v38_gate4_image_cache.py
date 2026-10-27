# -*- coding: utf-8 -*-
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))

import tempfile
from pathlib import Path
from unittest.mock import patch

import autopost as A
import dulieu as DL


class Resp:
    status_code = 201
    text = ''
    def __init__(self, media_id):
        self.media_id = media_id
    def json(self):
        return {'id': self.media_id, 'source_url': f'https://mock.local/media/{self.media_id}.webp'}


def main():
    with tempfile.TemporaryDirectory(prefix='snl-g4-') as td:
        DL.DB = Path(td) / 'du-lieu.db'
        p = Path(td) / 'same-name.webp'
        calls = []

        def fake_post(url, **kwargs):
            calls.append(kwargs.get('data', b''))
            return Resp(100 + len(calls))

        p.write_bytes(b'AAA-first-image')
        with patch.object(A, '_auth', return_value=('https://mock.local', None)), \
             patch('requests.post', side_effect=fake_post):
            first = A._url_anh_tren_wp('mock-site', p, tra_media_id=True)
            same = A._url_anh_tren_wp('mock-site', p, tra_media_id=True)
            p.write_bytes(b'BBB-replaced-image')
            replaced = A._url_anh_tren_wp('mock-site', p, tra_media_id=True)

        print('FIRST=', first)
        print('SAME=', same)
        print('REPLACED=', replaced)
        print('POST_CALLS=', len(calls))
        print('BYTES=', calls)
        assert first == same == (101, 'https://mock.local/media/101.webp')
        assert replaced == (102, 'https://mock.local/media/102.webp')
        assert len(calls) == 2
        assert calls == [b'AAA-first-image', b'BBB-replaced-image']
        print('PASS: media_id thật được trả; cùng hash skip; cùng tên nhưng hash khác upload lại')


if __name__ == '__main__':
    main()
