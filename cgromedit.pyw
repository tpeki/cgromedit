import TkEasyGUI as sg
import os.path as pa
from PIL import Image, ImageTk
import struct

NoImg = None
Regeon = 'JP'

class Fontset:
    # キャラジェネデータ
    num = 512  # 収容文字数(80Kなどの256パターンには未対応(FFS))
    rom = [0]*4096  # 生データ 8Byte x 512文字をリザーブ
    cpat = [None]*512  # 表示用イメージ(ImageTk.PhotoImage)/倍寸

    def __init__(self, rom=None):
        if rom is None:
            self.num = 512
            self.rom = [0]*4096
            for x in range(self.num):
                self.cpat[x] = None
        else:
            if len(rom) < 2048:
                return None
            elif len(rom) < 4096:
                self.num = 256
            else:
                self.num = 512
            for x in range(len(rom)):
                self.rom[x] = rom[x]
            for c in range(self.num):
                self.cpat[c] = twimage(rom[c*8:c*8+8])

    def setpattern(self, chr_no, pattern):
        # コードchr_noの文字としてpatternを書き込む
        if (self.rom is None) or (chr_no >= self.num) or (len(pattern) != 8):
            return None
        for x in range(8):
            self.rom[chr_no*8+x] = pattern[x]
        self.cpat[chr_no] = twimage(pattern)

        return chr_no


def read_CGROM():
    # MZ700winで利用するFONT700.JP形式のROMデータを読み込む
    # 4KB 512文字(0～0x1ff)分 0x100以降はひらがなCG
    if Regeon == 'JP':
        fty=(('CGROM File(JP)', '*.jp'),
             ('CGROM File(EU)', '*.dat'),
             ('Any File', '*.*'))
    else:
        fty=(('CGROM File(EU)', '*.dat'),
             ('CGROM File(JP)', '*.jp'),
             ('Any File', '*.*'))

    filename = sg.popup_get_file(message='Choose file:',
                                 title='CGROM File?',
                                 file_types=fty)

    if (filename == '') or (pa.getsize(filename) < 2048):
        return None

    size=2048  # 256 chrs
    if pa.getsize(filename) >= 4096:
        size=4096  # 512chrs
        
    buf = b''
    with open(filename, mode='rb') as rom:
        buf = rom.read(size)

    return buf


def save_CGROM(rom):
    # データをバイナリファイルに書き出す
    siz = len(rom) // 8
    if siz < 256:
        return 0

    if Regeon == 'JP':
        fty=(('CGROM File(JP)', '*.jp'),
             ('CGROM File(EU)', '*.dat'),
             ('Any File', '*.*'))
    else:
        fty=(('CGROM File(EU)', '*.dat'),
             ('CGROM File(JP)', '*.jp'),
             ('Any File', '*.*'))

    filename = sg.popup_get_file(message='Save file name:',
                                 title='Save CG-ROM', save_as=True,
                                 file_types=fty)
    if filename == '':
        return 0
    if pa.splitext(filename)[1] == '':
        filename += '.jp' if Regeon == 'JP' else '.dat'

    out = 0
    with open(filename, mode='wb+') as fo:
        for b in rom:
            out += fo.write(struct.pack('B',b))
    return out


def read_cgtxt():
    # テキスト表現のデータを読み込む
    # コードは0x1FFまで 順不同、不足していても良い
    fty=(('Text File', '*.txt'),
         ('Any File', '*.*'))
    filename = sg.popup_get_file(message='Choose file:',
                                 title='Import from Text File',
                                 file_types=fty)
    if filename == '':
        return None

    buf = []
    rc = 0
    with open(filename, mode='r', encoding='cp932', newline=None) as fi:
        buf = fi.read().splitlines()

    print('read_cgtxt: read %d lines'%len(buf))
    rom = [None] *4096
    l = 0
    while l < len(buf):
        line = buf[l]
        print('check %d'%l)
        if (line == '') or (line[0] != '#'):
            # 先頭が#の行まで読み飛ばす
            l += 1
            continue
        else:
            # 行頭#に続いてキャラジェネコード(0x16進か10進)
            # 0x100以降はひらがなCG
            if line[1:3].lower() == '0x':
                c = int(line[1:],16)
            else:
                c = int(line[1:])

            if (c&~0x1ff != 0):
                l += 1
                continue

        for x in range(8):
            t = buf[l+1+x]
            d = 0
            for p in range(8):
                d = d<<1
                if t[p] != '.':
                    d += 1
            rom[c*8+x] = d
        rc += 1
        l += 9

    print('read %d chars'%rc)
    return rom


def mk_cgtxt(rom):
    # テキスト表現でデータを書き出す
    fty=(('Text File', '*.txt'),
         ('Any File', '*.*'))
    filename = sg.popup_get_file(message='Choose file:',
                                 title='Export to Text File',
                                 save_as=True,
                                 file_types=fty)
    if filename == '':
        return 0
    if pa.splitext(filename)[1] == '':
        filename += '.txt'
        
    chrs = len(rom)//8
    if chrs < 256:
        return 0
    
    with open(filename, mode='w+', encoding='cp932') as f:
        for chr in range(chrs):
            f.write('#0x%03X\n'%chr)
            for byt in range(8):
                b=rom[chr*8+byt]
                for bit in range(8):
                    f.write( 'o' if (b & 128>>bit) else '.')
                f.write('\n')
            f.write('\n')

    return chrs


def fmap_mesh(fmap, mesh='#888800', text='#dddddd'):
    # フォントマップ部の罫線を引く
    for x in range(17):
        fmap.create_line(30, x*16+30, 286, x*16+30, fill=mesh)
        fmap.create_line(330, x*16+30, 586, x*16+30, fill=mesh)
        if x < 16:
            fmap.create_text(20, x*16+36, text='%X0'%x, fill=text)
            fmap.create_text(320, x*16+36, text='%X0'%x, fill=text)
        fmap.create_line(x*16+30, 30, x*16+30, 286, fill=mesh)
        fmap.create_line(x*16+330, 30, x*16+330, 286, fill=mesh)
        if x < 16:
            fmap.create_text(x*16+36, 20, text='+%X'%x, fill=text)
            fmap.create_text(x*16+336, 20, text='+%X'%x, fill=text)
    return


def fedt_mesh(fedit, mesh='#aaaaaa'):
    # フォントエディタ部の罫線を引く
    for x in range(9):
        fedit.create_line(0, x*16, 128, x*16, fill=mesh) 
        fedit.create_line(x*16, 0, x*16, 128, fill=mesh) 

    return


def noimg():
    # フォントマップ部の文字が無い部分のパターン
    # イメージがローカルのままだと解放されてしまって
    # Canvas.create_imageで表示したのに消えてしまうため、Globalに保存
    # 元は毎回生成してたがsingletonにする
    global NoImg

    if NoImg is None:
        im = Image.new('RGBA', (16,16))
        plot = (0xcc,0xcc,0xcc,255)
    
        for x in range(16):
            im.putpixel((x,x),plot)
            im.putpixel((15-x,x),plot)

        NoImg = ImageTk.PhotoImage(image=im)
    return NoImg

def twimage(byts, fore_color=(255,255,255), back_color=(0,0,0)):
    # fontmap部に表示するPhotoImageを生成
    # 作ったイメージはmainでFontset.cpatで保持する(しないと消える)
    im=Image.new('RGBA', (16,16))
    plot = fore_color+(255,)
    blank = back_color+(0,)

    # print('Data=', end='')
    for y in range(8):
        b=byts[y]
        # print('%02x '%b, end='')
        for x in range(8):
            if (b & 128>>x):
                im.putpixel((x*2,y*2), plot)
                im.putpixel((x*2+1,y*2), plot)
                im.putpixel((x*2,y*2+1), plot)
                im.putpixel((x*2+1,y*2+1), plot)
            else:
                im.putpixel((x*2,y*2), blank)
                im.putpixel((x*2+1,y*2), blank)
                im.putpixel((x*2,y*2+1), blank)
                im.putpixel((x*2+1,y*2+1), blank)
    # print('')
    return ImageTk.PhotoImage(image=im)


def box16(color=(0,0,0), alpha=255):
    """ box88(color) if color==(0,0,0), alpha=0"""
    # Fontedit部のpixel表示に使用するPhotoImage
    if alpha == 0:
        im = Image.new('RGBA',(15,15), color=(0,0,0,0))
    else:
        im = Image.new('RGBA',(15,15), color=color+(255,))
    return ImageTk.PhotoImage(image=im)
    

def putfont(fmap, chr_no, tkphoto):
    # 指定した文字番号の位置に文字イメージ(倍寸)を表示
    pg = 0 if chr_no < 0x100 else 1
    x = chr_no % 16
    y = (chr_no//16) % 16
    t = 'font%03X'%chr_no
    fmap.delete(t)
    fmap.create_image(38+x*16+pg*300, 38+y*16, image=tkphoto, tag=t)
    return


def view_rom(wn, fontset):
    # ROMイメージをFontmap部に一括表示
    cvs = wn['-cvs-']
    for i in range(fontset.num):
        tim = fontset.cpat[i]
        if tim is None:
            putfont(cvs, i, noimg())
        else:
            putfont(cvs, i, tim)
    return


def extract(ptn):
    # ROMデータをpixel毎の8x8配列に展開
    buf = [0]*64
    
    for y in range(8):
        b = ptn[y]
        for x in range(8):
           # buf[y*8+x] = box16(alpha=255 if (b & 128>>x) else 0)
           buf[y*8+x] = 1 if (b & 128>>x) else 0
    return buf


def setmask(fmap, disabled=False, mask=None):
    # edit時、fontmap部の表示を暗くする
    fmap.delete('mask')
    if (mask is None) or (len(mask) != 2):
        dis = Image.new('RGBA', (600,300), color=(0,0,0,80))
        ena = Image.new('RGBA', (600,300), color=(0,0,0,0))
        
        mask = [ImageTk.PhotoImage(image=dis),
                ImageTk.PhotoImage(image=ena)]

    if disabled:
        fmap.create_image(300, 150, image=mask[0], tag='mask')
    else:
        fmap.create_image(300, 150, image=mask[1], tag='mask')

    return mask


def ptn2txt(ptn):
    # Edit中のROMデータ16進表記用文字列生成
    ptxt = ''
    for y in range(4):
        ptxt += '0x%02X, 0x%02X,\n'%(ptn[y*2], ptn[y*2+1])
    return ptxt


def dots2bytes(dots):
    # 8x8配列のパターンイメージを8バイトのROMデータに変換
    out = [0]*8
    for i in range(8):
        byte = dots[i*8:i*8+8]
        bstr = ''.join(str(bit) for bit in byte)

        out[i] = int(bstr, 2)
    return out


def strtoix(s):
    if len(s) < 2:
        return int(s)
    if s[:2].upper() == '0X':
        return int(s,16)
    else:
        return int(s)


def cpinfo(prmpt):
    fromchr = [sg.Text(prmpt+'元コード:'),
               sg.Input(key='-fr-', default_text='0x000', expand_x=True)]
    tochr = [sg.Text(prmpt+'先コード:'),
             sg.Input(key='-to-', default_text='0x100', expand_x=True)]
    transsiz = [sg.Text(prmpt+'文字数:'),
                sg.Input(key='-sz-', default_text='1', expand_x=True)]
    buttons = [sg.Text('',expand_x=True),
               sg.Button('Cancel', key='-can-', size=(12,1)),
               sg.Button('Copy', key='-go-', size=(12,1))]

    lo = [[sg.Column(layout=[fromchr, tochr], anchor='nw'),
           sg.Column(layout=[transsiz], anchor='nw')],
          buttons]
    
    wn = sg.Window('パターン'+prmpt, layout=lo)

    fr, sz, to = 0, 0, 0
    while True:
        e,v = wn.read()
        if (e == sg.WINDOW_CLOSED) or (e == '-can-'):
            break
        elif e == '-go-':
            fr = strtoix(wn['-fr-'].get())
            to = strtoix(wn['-to-'].get())
            sz = strtoix(wn['-sz-'].get())
            break

    wn.close()
    return fr,sz,to


def fedit(wn, fontset, chr_no):
    # エディットモード
    fed = wn['-fnt-']
    ptn = fontset.rom[chr_no*8:chr_no*8+8]
    
    wn['-edok-'].update(disabled=False)
    wn['-edcan-'].update(disabled=False)
    wn['-fno-'].update(text='0x%03X'%chr_no)
    wn['-bytes-'].update(text=ptn2txt(ptn))

    b_on = box16(alpha=255)
    b_off = box16(alpha=0)
    fed.delete('pixels')
    dots = extract(ptn)
    
    for y in range(8):
        for x in range(8):
            fed.create_image(x*16+8, y*16+8,
                             image=b_on if dots[y*8+x]==1 else b_off,
                             tag=('pixels','p%d%d'%(x,y)))

    while True:
        e,v = wn.read()

        if e == sg.WINDOW_CLOSED:
            return sg.WINDOW_CLOSED
        elif e == '-edcan-':
            ptn = None
            break
        elif e == '-edok-':
            break
        elif e == '-fnt-rls':
            x = wn['-fnt-'].user_bind_event.x // 16
            y = wn['-fnt-'].user_bind_event.y // 16
            b = wn['-fnt-'].user_bind_event.num
            if b == 1:
                print(dots[y*8+x])
                dots[y*8+x] = 1 if dots[y*8+x] == 0 else 0
                fed.delete('p%d%d'%(x,y))
                fed.create_image(x*16+8, y*16+8,
                             image=b_on if dots[y*8+x]==1 else b_off,
                             tag=('pixels','p%d%d'%(x,y)))
                ptn = dots2bytes(dots)
                wn['-bytes-'].update(text=ptn2txt(ptn))
                
        print(e, v)

    wn['-bytes-'].update(text='')
    wn['-fno-'].update(text='')
    wn['-edok-'].update(disabled=True)
    wn['-edcan-'].update(disabled=True)
    return ptn


#
# MZ-700 Font CGROM data editor
#
if __name__ == '__main__':
    # フォントマップ部
    fontmap = sg.Canvas(key='-cvs-', size=(600, 300),
                        background_color='#4444ff', anchor='nw')
    fontmap.bind("<ButtonPress>", "prs")
    fontmap.bind("<ButtonRelease>", "rls")        

    # Edit部の画面も作ってしまう(マウスイベントも)
    fontedit = sg.Canvas(key='-fnt-', size=(128, 128),
                         background_color='#ffffff')
    fontedit.bind("<ButtonPress>", "prs")
    fontedit.bind("<ButtonRelease>", "rls")        
    fontno = sg.Text('', background_color='#ffffff', size=(6,1), key='-fno-')
    fontdata = sg.Multiline(text='', key='-bytes-',
                            size=(12,6))
    editpane = [[fontedit],
                [sg.Text('Chr No='),fontno],
                [fontdata],
                [sg.Text('',expand_x=True),
                 sg.Button('can', key='-edcan-', disabled=True),
                 sg.Button('Done', key='-edok-', disabled=True)],
                ]

    # メニューバー
    menu_items = [['File',['Open CG::-opnrom-',
                           'Clear::-cls-',
                           '---',
                           'Save CG::-svrom-',
                           '---',
                           'Exit::-exit-']],
                  ['Text File', ['Import::-imptxt-',
                                 'Append::-apdtxt-',
                                 'Export::-exttxt-']],
                  ['Tool',['Copy::-cpytl-',
                           'Swap::-swptl-',]]
                  ]

    lo = [[sg.Menu(menu_items, key='-mnu-')],
          [sg.Text('Character Generator ROM Editor for MZ700'),
           sg.Text('',expand_x=True),sg.Text('Size=512', key='-siz-')],
          [fontmap, sg.Column(layout=editpane, vertical_alignment='top')]
          ]
    wn = sg.Window('MZ-700 CGROM', layout=lo,
                   expand_x=True, expand_y=True)

    # 罫線引いとく
    fmap_mesh(fontmap, mesh='#888800', text='#dddddd')    
    mask = setmask(fontmap, disabled=False)
    fedt_mesh(fontedit, mesh='#aaaaaa')

    # ROMが読まれていないのでfontmapも空文字表示
    nim = noimg()
    for x in range(512):
        putfont(fontmap, x, nim)

    # Main Loop
    while True:
        e,v = wn.read()
        
        if (e == sg.WINDOW_CLOSED) or (e == '-exit-'):
            break
        elif e == '-opnrom-':
            romimg = read_CGROM()
            if romimg is not None:
                fontset = Fontset(romimg)
                view_rom(wn, fontset)
        elif e == '-cls-':
            if sg.confirm('CGROMデータを初期化します', title=''):
                fontset=Fontset()
                view_rom(wn, fontset)
        elif e == '-svrom-':
            save_CGROM(fontset.rom)
        elif e == '-imptxt-':
            romimg = read_cgtxt()
            if romimg is not None:
                romimg = [0 if romimg[i] is None else romimg[i]
                          for i in range(len(romimg))]
                fontset = Fontset(romimg)
                view_rom(wn, fontset)
        elif e == '-apdtxt-':
            romimg = read_cgtxt()
            if romimg is not None:
                for c in range(len(romimg)//8):
                    if romimg[c*8] is not None:
                        fontset.setpattern(c, romimg[c*8:c*8+8])
                view_rom(wn, fontset)
        elif e == '-exttxt-':
            mk_cgtxt(fontset.rom)
        elif e == '-cpytl-':
            setmask(fontmap, disabled=True, mask=mask)
            fr,sz,to = cpinfo('コピー')
            setmask(fontmap, disabled=False, mask=mask)

            if (fr == to) or (sz <= 0):
                continue
            if fr > to:
                for i in range(sz):
                    pat = fontset.rom[(fr+i)*8:(fr+i)*8+8]
                    fontset.setpattern(to+i, pat)
            elif fr < to:
                for i in range(sz):
                    r=sz-i-1
                    pat = fontset.rom[(fr+r)*8:(fr+r)*8+8]
                    fontset.setpattern(to+r, pat)
            view_rom(wn, fontset)
        elif e == '-swptl-':
            setmask(fontmap, disabled=True, mask=mask)
            fr,sz,to = cpinfo('入替')
            setmask(fontmap, disabled=False, mask=mask)

            if (fr == to) or (sz <= 0):
                continue
            if (fr < to < (fr+sz)) or (to < fr < (to+sz)):
                print('交換区間がコンフリクトしています')
                continue

            tor = fontset.rom[to*8:(to+sz)*8+8]
            for i in range(sz):
                pat = fontset.rom[(fr+i)*8:(fr+i)*8+8]
                fontset.setpattern(to+i, pat)
                pat = tor[i*8:i*8+8]
                fontset.setpattern(fr+i, pat)
            view_rom(wn, fontset)
        elif e == '-cvs-rls':
            # Mapの文字クリックでエディットモードに
            if 'fontset' not in dir():
                print('Not yet read fontset.')
                continue
            x = wn['-cvs-'].user_bind_event.x
            y = wn['-cvs-'].user_bind_event.y
            b = wn['-cvs-'].user_bind_event.num
            cp = 1 if x > 300 else 0
            cx = (x-30 - (300*cp)) // 16
            cy = (y-30) // 16
            if (b==1) and (cx&~0xf == 0) and (cy&~0xf == 0):
                chr_no = cp*256 + cy*16 + cx
            else:
                print('not chr position')
                continue
            
            setmask(fontmap, disabled=True, mask=mask)
            ptn = fedit(wn, fontset, chr_no)
            setmask(fontmap, disabled=False, mask=mask)

            if ptn == sg.WINDOW_CLOSED:
                break
            elif (ptn is None) or (len(ptn) != 8):
                continue

            fontset.setpattern(chr_no, ptn)
            putfont(wn['-cvs-'], chr_no, fontset.cpat[chr_no])
        else:
            if not '-prs' in e:
                print(e, v)

    wn.close()
