import sys, tempfile, shutil, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFilter
import xu_ly_anh as X

with tempfile.TemporaryDirectory() as td:
    p=Path(td)
    sharp=Image.new('RGB',(1200,1000),'white'); d=ImageDraw.Draw(sharp)
    for x in range(0,1200,30): d.line((x,0,x,1000),fill='black',width=3)
    for y in range(0,1000,30): d.line((0,y,1200,y),fill='black',width=3)
    sharp.save(p/'sharp.jpg',quality=95)
    shutil.copy2(p/'sharp.jpg',p/'duplicate.jpg')

    small=Image.new('RGB',(500,500),'white'); ds=ImageDraw.Draw(small)
    for x in range(0,500,20): ds.line((x,0,x,500),fill='black',width=2)
    small.save(p/'small.jpg',quality=95)

    blur=sharp.filter(ImageFilter.GaussianBlur(14)); blur.save(p/'blur.jpg',quality=95)
    (p/'garbage.txt').write_text('not image',encoding='utf-8')

    sv=X.laplacian_variance(p/'sharp.jpg'); bv=X.laplacian_variance(p/'blur.jpg')
    kq=X.loc_kho_anh(p)
    print(f'SHARP_LAPLACIAN={sv:.3f}; BLUR_LAPLACIAN={bv:.3f}; THRESHOLD={X.NGUONG_MO_LAPLACIAN}')
    print('COUNTS='+json.dumps({'in':kq['tong_file'],'image_in':kq['anh_hop_le_dau_vao'],'out':kq['giu_lai'],**kq['loai']},ensure_ascii=False))
    assert sv > X.NGUONG_MO_LAPLACIAN and bv < X.NGUONG_MO_LAPLACIAN
    assert kq['tong_file']==5
    assert kq['giu_lai']==1
    assert kq['loai']=={'khong_phai_anh':1,'trung_byte':1,'anh_nho':1,'anh_mo':1}
    assert (p/'sharp.jpg').exists() and (p/'duplicate.jpg').exists() and (p/'small.jpg').exists() and (p/'blur.jpg').exists()
    out=p/'_DA_LOC'
    kept=[x for x in out.glob('*.jpg')]
    assert len(kept)==1, kept
    assert (out/'bao-cao-loc-anh.json').exists()
    print('ORIGINAL_FILES_UNTOUCHED=PASS; OUTPUT_FOLDER=_DA_LOC; REPORT=PASS')
print('PASS V40-2 IMAGE FILTER')
