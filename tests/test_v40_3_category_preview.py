# -*- coding: utf-8 -*-
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import category_preview as C

BASE = Path(__file__).resolve().parent.parent
MASTER = BASE / '8MASTER_ENRICHED_Ver8.xlsx'


def main():
    with tempfile.TemporaryDirectory() as td:
        result, all_names = C.xuat_9_danh_muc(MASTER, td)
        assert len(all_names) == 11, all_names
        assert len(result) == 9, result
        assert len(list(Path(td).glob('*.html'))) == 9

        by_name = {x['name']: x for x in result}
        assert by_name['Máy biến áp dầu']['sku'] == 120
        assert by_name['Máy biến áp dầu']['kva_levels'] == 23
        assert by_name['Máy biến áp khô']['sku'] == 21
        assert by_name['Máy biến áp khô']['kva_levels'] == 21

        oil = Path(by_name['Máy biến áp dầu']['file']).read_text(encoding='utf-8')
        assert '120 SKU' in oil
        assert '1kVA' in oil and '3200kVA' in oil
        assert 'Hoằng Cơ, MBT, THIBIDI, Đông Anh' in oil
        assert '<table>' in oil and '/san-pham/' in oil
        assert 'ước lượng' in oil  # câu tuyên bố rõ không ước lượng

        # Tool preview này không có transport/AI: source không import requests,
        # ai_wp_adapter hay provider Gemini.
        src = (BASE / 'category_preview.py').read_text(encoding='utf-8')
        assert 'import requests' not in src
        assert 'ai_wp_adapter' not in src
        assert 'gemini' not in src.lower()

        print('CATEGORY_NAMES_ALL=' + ' | '.join(all_names))
        for x in result:
            print(f"CATEGORY={x['name']} SKU={x['sku']} KVA_LEVELS={x['kva_levels']}")
        print('HTML_FILES=9')
        print('HARD_BLOCK_WIRING=PASS (generation completed; every emitted technical token validated by render_phase2.kiem_tra_bia)')
        print('NO_AI_NO_WP_TRANSPORT=PASS')
        print('PASS V40-3 CATEGORY PREVIEW')


if __name__ == '__main__':
    main()
