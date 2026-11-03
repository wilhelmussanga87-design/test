# -*- coding: utf-8 -*-
"""Dashboard Pengendalian SATRIA Puslitbang - aplikasi lokal (Streamlit).

Dipakai KPA (Kapuslitbang), Urkeu, Pokja, dan PPK untuk pengendalian anggaran,
risiko, kontrak, milestone, serta pencatatan keputusan KPA. Seluruh perubahan
data tercatat pada tabel audit. Aplikasi berjalan offline/LAN tanpa internet.
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

import base64
import html
import os

import db
import impor

_HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(_HERE, "assets")
_IKON = os.path.join(ASSET, "satria_favicon.png")

st.set_page_config(page_title="Dashboard Pengendalian SATRIA - Puslitbang Polri",
                   page_icon=(_IKON if os.path.exists(_IKON) else "\U0001F4CA"),
                   layout="wide")

# ----------------------------------------------------------- aset & tema ----

# folder dokumen output Proyek Perubahan (3 Pilar Output SATRIA + Matriks Alur & Deadline)
# Disimpan di dalam paket aplikasi agar tetap terbaca saat folder dipindah/dibawa ke Bandung.
PILAR_DIR = os.path.join(ASSET, "pilar")
PILAR_DIR_LUAR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "2. LPP PKN II TH 2026", "3 Pilar Output SATRIA")
DOKUMEN_PILAR = [
    "04. Matriks Alur Proses dan Deadline - SATRIA Puslitbang.docx",
    "01. SOP Percepatan Pengadaan Pra-DIPA dan Mitigasi Transisi KPA - SATRIA Puslitbang.docx",
    "02. Risk Register Kinerja - SATRIA Puslitbang.docx",
    "03. Kartu Kendali Bulanan KPA Berbasis Risiko - SATRIA Puslitbang.docx",
]


def _aset(nama):
    """Isi berkas aset sebagai bytes; None bila tidak ada (aplikasi tetap jalan)."""
    try:
        with open(os.path.join(ASSET, nama), "rb") as f:
            return f.read()
    except OSError:
        return None


def _data_uri(nama):
    b = _aset(nama)
    if not b:
        return None
    ext = os.path.splitext(nama)[1].lower()
    if ext in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    elif ext == ".gif":
        mime = "image/gif"
    elif ext == ".woff2":
        mime = "font/woff2"
    elif ext == ".woff":
        mime = "font/woff"
    elif ext in (".ttf", ".otf"):
        mime = "font/ttf"
    else:
        mime = "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(b).decode())


def tema():
    """Tema visual SATRIA: gradasi warna hidup, aksen emas, foto gedung samar."""
    foto = _data_uri("gedung_band.jpg") or _data_uri("gedung_watermark.png") or ""
    font = _data_uri("fonts/plus-jakarta-sans.woff2") or ""
    css = """
<style>
    @font-face{
        font-family:'Plus Jakarta Sans';
        src:url('__FONT__') format('woff2');
        font-weight:200 800;font-style:normal;font-display:swap;
    }
    :root{
        --navy1:#0a1830; --navy2:#12294d; --navy3:#1d3d72; --navy4:#2f61b0;
        --gold:#e4b23c; --gold2:#f7d67e; --teal:#12a594; --red:#d64545;
        --green:#2e9e5b; --violet:#7a4dd6; --ink:#152238; --muted:#5c6b86;
        --line:#dde6f5;
    }
    /* ---------- latar aplikasi ---------- */
    [data-testid='stAppViewContainer']{
        background:
            radial-gradient(1100px 460px at 100% -8%, rgba(47,97,176,.20), transparent 62%),
            radial-gradient(900px 420px at -8% 6%, rgba(228,178,60,.16), transparent 58%),
            linear-gradient(180deg,#eef3fb 0%,#e7eef9 55%,#eaf1fb 100%);
        background-attachment:fixed,fixed,fixed;
    }
    [data-testid='stAppViewContainer']::before{
        content:"";position:fixed;right:-70px;bottom:-60px;width:600px;height:340px;
        background:url('__BGN__') no-repeat center/contain;opacity:.09;
        pointer-events:none;z-index:0;
    }
    [data-testid='stHeader']{background:transparent;}
    /* ---------- sidebar ---------- */
    [data-testid='stSidebar']{
        background:linear-gradient(185deg,#0a1830 0%,#12294d 45%,#1d3d72 78%,#27488a 100%);
        border-right:1px solid rgba(247,214,126,.18);
    }
    [data-testid='stSidebar'] *{color:#eef3fb;}
    [data-testid='stSidebar'] [data-testid='stCaptionContainer']{color:#b7c7e4;}
    [data-testid='stSidebar'] hr{border-color:rgba(247,214,126,.35);}
    [data-testid='stSidebar'] .satria-side-kop{display:flex;align-items:center;gap:10px;
        background:rgba(255,255,255,.07);border:1px solid rgba(247,214,126,.30);
        border-radius:14px;padding:10px;margin-bottom:8px;}
    [data-testid='stSidebar'] .satria-side-kop img.pb{height:46px;width:auto;}
    [data-testid='stSidebar'] .satria-side-kop img.st{height:38px;width:auto;
        filter:drop-shadow(0 2px 6px rgba(247,214,126,.5));}
    [data-testid='stSidebar'] .satria-side-kop .t{font-weight:800;font-size:1.02rem;line-height:1.1;}
    [data-testid='stSidebar'] .satria-side-kop .s{font-size:.66rem;color:#b7c7e4;}
    [data-testid='stSidebar'] .stButton>button{
        background:linear-gradient(90deg,rgba(247,214,126,.18),rgba(47,97,176,.30));
        border:1px solid rgba(247,214,126,.45);color:#fff;font-weight:600;}
    [data-testid='stSidebar'] .stButton>button:hover{border-color:#f7d67e;color:#12294d;}
    /* ---------- judul ---------- */
    h1,h2,h3,h4,h5{color:var(--navy2);letter-spacing:.1px;}
    h3{border-left:5px solid var(--gold);padding-left:12px;}
    /* ---------- kartu metrik berwarna ---------- */
    div[data-testid='stMetric']{
        background:linear-gradient(180deg,#ffffff,#f6f9ff);
        border:1px solid var(--line);border-top:5px solid var(--navy3);
        border-radius:14px;padding:10px 14px;
        box-shadow:0 3px 10px rgba(18,41,77,.07);
        transition:transform .14s,box-shadow .14s;}
    div[data-testid='stMetric']:hover{transform:translateY(-3px);
        box-shadow:0 10px 22px rgba(18,41,77,.16);}
    div[data-testid='stMetricValue']{color:var(--navy2);}
    [data-testid='stHorizontalBlock']>div:nth-child(1) div[data-testid='stMetric']{border-top-color:#1d3d72;}
    [data-testid='stHorizontalBlock']>div:nth-child(2) div[data-testid='stMetric']{border-top-color:#12a594;}
    [data-testid='stHorizontalBlock']>div:nth-child(3) div[data-testid='stMetric']{border-top-color:#e4b23c;}
    [data-testid='stHorizontalBlock']>div:nth-child(4) div[data-testid='stMetric']{border-top-color:#d64545;}
    [data-testid='stHorizontalBlock']>div:nth-child(5) div[data-testid='stMetric']{border-top-color:#7a4dd6;}
    /* ---------- tombol ---------- */
    .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{
        background:linear-gradient(90deg,#1d3d72,#2f61b0);color:#fff;border:0;
        border-radius:10px;font-weight:600;padding:.45rem 1.05rem;
        box-shadow:0 3px 8px rgba(29,61,114,.28);transition:.14s;}
    .stButton>button:hover,.stDownloadButton>button:hover,.stFormSubmitButton>button:hover{
        background:linear-gradient(90deg,#e4b23c,#f7d67e);color:#12294d;
        box-shadow:0 6px 16px rgba(228,178,60,.45);}
    /* ---------- tabel & expander ---------- */
    [data-testid='stDataFrame'],[data-testid='stTable']{border-radius:12px;overflow:hidden;
        border:1px solid var(--line);}
    details[data-testid='stExpander']{border:1px solid var(--line);border-radius:12px;
        background:rgba(255,255,255,.75);}
    /* ---------- hero ---------- */
    .satria-hero{position:relative;border-radius:20px;overflow:hidden;margin-bottom:14px;
        border:1px solid rgba(247,214,126,.45);
        box-shadow:0 14px 34px rgba(10,24,48,.30);}
    .satria-hero .foto{position:absolute;inset:0;background-size:cover;
        background-position:center;opacity:.55;}
    .satria-hero .tudung{position:absolute;inset:0;
        background:linear-gradient(115deg,rgba(10,24,48,.95) 0%,rgba(18,41,77,.86) 46%,
        rgba(47,97,176,.72) 100%);}
    .satria-hero .isi{position:relative;z-index:2;display:flex;align-items:center;gap:18px;
        padding:16px 22px;min-height:134px;}
    .satria-hero .lgo{flex:0 0 auto;display:flex;align-items:center;justify-content:center;
        width:104px;height:104px;border-radius:18px;background:rgba(255,255,255,.96);
        box-shadow:0 6px 16px rgba(0,0,0,.25);}
    .satria-hero .lgo img{max-width:88px;max-height:88px;}
    .satria-hero .lgo.satria{background:transparent;box-shadow:none;width:122px;height:122px;}
    .satria-hero .lgo.satria img{max-width:122px;max-height:122px;
        filter:drop-shadow(0 4px 14px rgba(247,214,126,.6));}
    .satria-hero .teks{flex:1;min-width:0;}
    .satria-hero .lembaga{color:var(--gold2);font-size:.78rem;font-weight:700;
        letter-spacing:2.4px;text-transform:uppercase;}
    .satria-hero .judul{color:#fff;font-size:1.48rem;font-weight:800;line-height:1.2;
        margin-top:2px;}
    .satria-hero .sub{color:#d7e2f5;font-size:.85rem;margin-top:3px;}
    .satria-hero .chip{display:inline-flex;align-items:center;gap:6px;margin-top:9px;
        margin-right:6px;background:rgba(255,255,255,.12);
        border:1px solid rgba(247,214,126,.42);color:#fff;font-size:.72rem;
        padding:3px 11px;border-radius:999px;}
    /* ---------- kartu fitur ---------- */
    .satria-fitur{display:flex;gap:12px;flex-wrap:wrap;margin:4px 0 8px;}
    .satria-fitur .k{flex:1 1 210px;border-radius:14px;padding:12px 14px;background:#fff;
        border:1px solid var(--line);border-left:6px solid var(--navy3);
        box-shadow:0 3px 10px rgba(18,41,77,.06);}
    .satria-fitur .k h4{margin:0 0 4px;color:var(--navy2);font-size:.97rem;}
    .satria-fitur .k p{margin:0;color:var(--muted);font-size:.79rem;line-height:1.35;}
    .satria-fitur .k.teal{border-left-color:var(--teal);}
    .satria-fitur .k.gold{border-left-color:var(--gold);}
    .satria-fitur .k.red{border-left-color:var(--red);}
    /* ---------- bingkai foto ---------- */
    .satria-bangku{border-radius:14px;overflow:hidden;margin-bottom:10px;
        border:1px solid var(--line);box-shadow:0 4px 14px rgba(18,41,77,.14);}
    .satria-bangku img{width:100%;display:block;}
    .satria-label{background:linear-gradient(90deg,#12294d,#2f61b0);color:#fff;
        font-size:.78rem;padding:7px 12px;}
    /* ---------- footer ---------- */
    .satria-kaki{margin-top:14px;padding:12px 16px;border-radius:14px;
        background:linear-gradient(90deg,#0a1830,#12294d 60%,#1d3d72);
        color:#cdd9ee;font-size:.78rem;display:flex;align-items:center;gap:14px;}
    .satria-kaki img{height:34px;width:auto;}
    .satria-kaki .g{flex:1;}
    .satria-kaki b{color:var(--gold2);}

    /* ============ TIPOGRAFI PRESISI - Plus Jakarta Sans ============ */
    :root{
        --font-ui:'Plus Jakarta Sans','Segoe UI Variable Text','Segoe UI',system-ui,
            -apple-system,'Helvetica Neue',Arial,sans-serif;
        --font-display:'Plus Jakarta Sans','Segoe UI Variable Display','Segoe UI',
            system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif;
    }
    html,body,[data-testid='stAppViewContainer'],[data-testid='stSidebar'],
    [data-testid='stMarkdown'],[data-testid='stMarkdownContainer'],
    [data-testid='stText'],[data-testid='stHeading'],
    .stMarkdown,.stMarkdown p,.stMarkdown li,.stCaptionContainer,
    .satria-hero,.satria-hero *,.satria-fitur,.satria-fitur *,
    .satria-galeri,.satria-galeri *,.satria-kaki,.satria-kaki *,
    .satria-bangku,.satria-bangku *,
    button,input,textarea,select,[data-baseweb='select'] div{
        font-family:var(--font-ui)!important;
    }
    html,body{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
        text-rendering:optimizeLegibility;}
    body{color:var(--ink);font-size:15px;line-height:1.62;letter-spacing:-.003em;
        font-feature-settings:"kern" 1,"liga" 1,"calt" 1;}
    ::selection{background:rgba(228,178,60,.32);color:var(--navy1);}
    code,pre,kbd,samp{font-family:'Cascadia Mono',Consolas,'Courier New',monospace!important;}

    h1,h2,h3,h4,h5,h6{
        font-family:var(--font-display)!important;color:var(--navy2);
        font-weight:800!important;letter-spacing:-.022em;line-height:1.26;
        text-wrap:balance;
    }
    h1{font-size:clamp(1.65rem,2.6vw,2.05rem);}
    h2{font-size:clamp(1.22rem,1.8vw,1.46rem);letter-spacing:-.018em;}
    h3{font-size:1.12rem;border-left:4px solid var(--gold);padding-left:12px;
        margin:1.1rem 0 .45rem;letter-spacing:-.012em;}
    h4{font-size:1.02rem;letter-spacing:-.008em;}
    h5{font-size:.92rem;letter-spacing:0;}
    p,li{font-size:.9rem;line-height:1.68;}
    [data-testid='stCaptionContainer'] p,.stCaptionContainer p{
        font-size:.75rem!important;line-height:1.55;color:var(--muted);
        letter-spacing:.006em;
    }
    [data-testid='stWidgetLabel'] p,label[data-testid='stWidgetLabel'] p,
    [data-testid='stWidgetLabel']{
        font-size:.79rem!important;font-weight:700!important;color:var(--navy2)!important;
        letter-spacing:.008em;
    }
    .stTextInput input,.stNumberInput input,.stTextArea textarea,
    .stSelectbox div[data-baseweb='select']>div{
        font-size:.86rem!important;font-weight:500;
    }
    .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{
        font-family:var(--font-ui)!important;font-size:.81rem;letter-spacing:.015em;
        font-weight:700;border-radius:10px;
    }
    /* angka selalu rata & presisi */
    [data-testid='stMetricValue'],[data-testid='stMetricDelta'],
    [data-testid='stDataFrame'],[data-testid='stTable'],
    .satria-kaki,.satria-hero .chip{
        font-variant-numeric:tabular-nums lining-nums;
    }
    div[data-testid='stMetric']{
        padding:12px 15px 11px;border-radius:15px;
        box-shadow:0 4px 14px rgba(18,41,77,.07);
    }
    [data-testid='stMetricLabel'],[data-testid='stMetricLabel'] p{
        font-size:.68rem!important;line-height:1.35!important;font-weight:700!important;
        letter-spacing:.055em;text-transform:uppercase;color:var(--muted)!important;
        margin-bottom:2px;
    }
    [data-testid='stMetricValue']{
        font-size:1.58rem!important;line-height:1.12!important;font-weight:800!important;
        letter-spacing:-.03em;color:var(--navy2)!important;
    }
    [data-testid='stMetricDelta']{font-size:.72rem!important;font-weight:700!important;}
    /* header hero */
    .satria-hero{border-radius:22px;}
    .satria-hero .isi{padding:18px 24px;min-height:142px;}
    .satria-hero .lembaga{font-size:.67rem;letter-spacing:.19em;font-weight:800;}
    .satria-hero .judul{
        font-size:clamp(1.3rem,2.35vw,1.72rem);letter-spacing:-.028em;line-height:1.16;
        font-weight:800;text-shadow:0 2px 10px rgba(0,0,0,.18);
    }
    .satria-hero .judul::after{content:"";display:block;width:56px;height:3px;
        margin-top:9px;border-radius:99px;
        background:linear-gradient(90deg,var(--gold),var(--gold2));}
    .satria-hero .sub{font-size:.82rem;line-height:1.55;max-width:68ch;color:#dbe6f7;}
    .satria-hero .chip{font-size:.67rem;font-weight:600;letter-spacing:.012em;}
    /* kartu fitur */
    .satria-fitur .k{border-radius:15px;padding:13px 15px;}
    .satria-fitur .k h4{font-size:.91rem;font-weight:800;letter-spacing:-.01em;line-height:1.35;}
    .satria-fitur .k p{font-size:.77rem;line-height:1.56;}
    /* sidebar */
    [data-testid='stSidebar'] .satria-side-kop .t{letter-spacing:-.015em;}
    [data-testid='stSidebar'] .satria-side-kop .s{letter-spacing:.01em;}
    [data-testid='stSidebar'] [data-testid='stCaptionContainer'],
    [data-testid='stSidebar'] [data-testid='stCaptionContainer'] p{
        color:#b7c7e4!important;font-size:.72rem!important;
    }
    [data-testid='stSidebar'] [data-testid='stWidgetLabel'],
    [data-testid='stSidebar'] [data-testid='stWidgetLabel'] *,
    [data-testid='stSidebar'] h1,[data-testid='stSidebar'] h2,
    [data-testid='stSidebar'] h3,[data-testid='stSidebar'] h4{
        color:#eef3fb!important;
    }
    [data-testid='stSidebar'] label[data-baseweb='radio'] p,
    [data-testid='stSidebar'] div[role='radiogroup'] p{
        font-size:.83rem!important;font-weight:600!important;letter-spacing:.005em;
    }
    /* detail kecil agar terasa rapi */
    [data-testid='stAlert']{border-radius:12px;}
    [data-testid='stAlert'] p{font-size:.84rem;line-height:1.55;}
    details[data-testid='stExpander'] summary{font-weight:700;font-size:.85rem;
        letter-spacing:.004em;}
    button[data-baseweb='tab']{font-weight:700;font-size:.82rem;letter-spacing:.012em;}
    /* pemisah lembut */
    hr{border:0;height:1px;background:linear-gradient(90deg,transparent,var(--line) 18%,
        var(--line) 82%,transparent);}
    /* footer */
    .satria-kaki{font-size:.74rem;line-height:1.55;letter-spacing:.004em;}
    .satria-kaki b{font-weight:800;letter-spacing:.005em;}
    /* scrollbar halus */
    ::-webkit-scrollbar{width:10px;height:10px;}
    ::-webkit-scrollbar-track{background:transparent;}
    ::-webkit-scrollbar-thumb{background:#c2d0e6;border:2px solid transparent;
        border-radius:99px;background-clip:content-box;}
    ::-webkit-scrollbar-thumb:hover{background:#9cb2d2;border:2px solid transparent;
        background-clip:content-box;}
    /* mode presentasi: kanvas bersih untuk proyektor */
    [data-testid='stToolbar'],[data-testid='stDecoration'],
    [data-testid='stStatusWidget'],#MainMenu,footer{display:none!important;}

    /* ============ GALERI VISUAL DASHBOARD ============ */
    .satria-galeri-kop{display:flex;align-items:flex-end;justify-content:space-between;
        gap:16px;flex-wrap:wrap;margin:20px 0 10px;}
    .satria-galeri-kop .eyebrow{color:#a87914;font-size:.66rem;font-weight:800;
        letter-spacing:.16em;text-transform:uppercase;}
    .satria-galeri-kop .judul{color:var(--navy2);font-size:1.24rem;font-weight:800;
        letter-spacing:-.02em;line-height:1.2;margin-top:2px;}
    .satria-galeri-kop .ket{color:var(--muted);font-size:.77rem;line-height:1.5;
        max-width:56ch;}
    .satria-galeri{columns:3;column-gap:14px;margin-top:4px;}
    .satria-galeri .pil{position:relative;break-inside:avoid;margin:0 0 14px;
        border-radius:16px;overflow:hidden;background:#0a1830;
        border:1px solid rgba(255,255,255,.72);
        box-shadow:0 6px 18px rgba(18,41,77,.15);
        transition:transform .18s ease,box-shadow .18s ease;}
    .satria-galeri .pil:hover{transform:translateY(-4px);
        box-shadow:0 16px 32px rgba(18,41,77,.26);}
    .satria-galeri .pil img{display:block;width:100%;height:auto;}
    .satria-galeri .tag{position:absolute;top:11px;left:11px;padding:3px 9px;
        border-radius:999px;background:rgba(10,24,48,.72);color:#f7d67e;
        border:1px solid rgba(247,214,126,.55);font-size:.62rem;font-weight:800;
        letter-spacing:.08em;text-transform:uppercase;backdrop-filter:blur(4px);}
    .satria-galeri .ket{position:absolute;left:0;right:0;bottom:0;padding:30px 13px 11px;
        background:linear-gradient(0deg,rgba(10,24,48,.94) 0%,
        rgba(10,24,48,.62) 58%,transparent 100%);color:#fff;}
    .satria-galeri .ket b{display:block;font-size:.84rem;font-weight:700;
        letter-spacing:.005em;line-height:1.3;}
    .satria-galeri .ket span{display:block;margin-top:2px;font-size:.69rem;
        color:#d3dff2;line-height:1.4;}
    @media (max-width:1100px){.satria-galeri{columns:2;}}
    @media (max-width:700px){
        .satria-galeri{columns:1;}
        .satria-galeri-kop{align-items:flex-start;}
        /* hero tetap ringkas di layar HP */
        .satria-hero .isi{flex-wrap:nowrap;gap:12px;padding:14px 16px;min-height:0;}
        .satria-hero .lgo{width:72px;height:72px;border-radius:14px;}
        .satria-hero .lgo img{max-width:58px;max-height:58px;}
        .satria-hero .lgo.satria{display:none;}
        .satria-hero .lembaga{font-size:.58rem;letter-spacing:.12em;}
        .satria-hero .judul{font-size:1.08rem;letter-spacing:-.018em;}
        .satria-hero .judul::after{width:42px;height:2px;margin-top:7px;}
        .satria-hero .sub{font-size:.74rem;line-height:1.5;}
        .satria-hero .chip{font-size:.6rem;padding:3px 9px;margin-top:7px;}
    }
</style>"""
    css = css.replace("__BGN__", foto).replace("__FONT__", font)
    st.markdown(css, unsafe_allow_html=True)


def kop(judul_teks, sub_teks):
    """Kepala halaman: foto gedung + logo Puslitbang Polri + emblem SATRIA terbaru."""
    logo = _data_uri("puslitbang_logo.png")
    satria = _data_uri("satria_logo.png") or _data_uri("satria_badge.png")
    # Latar hero memakai foto Gedung Puslitbang Polri (gedung_kapus -> gedung_band).
    foto = _data_uri("gedung_band.jpg") or _data_uri("hero.jpg") or _data_uri("bg_hero.png")
    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][date.today().weekday()]
    h = ["<div class='satria-hero'>"]
    if foto:
        h.append("<div class='foto' style=\"background-image:url('%s')\"></div>" % foto)
    h.append("<div class='tudung'></div><div class='isi'>")
    h.append("<div class='lgo'>%s</div>" %
             (("<img src='%s' alt='Puslitbang Polri'/>" % logo) if logo else "<b>POLRI</b>"))
    h.append("<div class='teks'>")
    h.append("<div class='lembaga'>Pusat Penelitian dan Pengembangan Polri</div>")
    h.append("<div class='judul'>%s</div>" % judul_teks)
    if sub_teks:
        h.append("<div class='sub'>%s</div>" % sub_teks)
    h.append("<div><span class='chip'>\U0001F4C5 %s, %s</span>"
             "<span class='chip'>\U0001F512 Aplikasi lokal - tanpa internet</span>"
             "<span class='chip'>\U0001F3AF TA 2026</span></div>" % (hari, tgl_id(date.today().isoformat())))
    h.append("</div>")
    h.append("<div class='lgo satria'>%s</div>" %
             (("<img src='%s' alt='SATRIA'/>" % satria) if satria else ""))
    h.append("</div></div>")
    st.markdown("".join(h), unsafe_allow_html=True)


def tiga_pilar():
    """Tiga instrumen SATRIA (SOP, Risk Register, Kartu Kendali KPA)."""
    st.markdown("""
<div class='satria-fitur'>
  <div class='k'><h4>1. SOP Percepatan Pengadaan Pra-DIPA</h4>
    <p>Kesiapan proses sejak dini &amp; mitigasi transisi kewenangan KPA -
    dokumen tervalidasi sesuai ketentuan.</p></div>
  <div class='k teal'><h4>2. Risk Register Kinerja</h4>
    <p>Antisipasi hambatan: skor Kemungkinan x Dampak, ambang Hijau/Kuning/Merah,
    mitigasi, PIC, dan tenggat.</p></div>
  <div class='k gold'><h4>3. Kartu Kendali Bulanan KPA</h4>
    <p>Kendali keputusan &amp; tindak lanjut: capaian paket, peringatan dini,
    dan arah KPA setiap bulan.</p></div>
</div>""", unsafe_allow_html=True)


def foto_bangunan(keterangan="Gedung Puslitbang Polri"):
    """Bingkai foto gedung Puslitbang Polri."""
    b = _data_uri("gedung_band.jpg") or _data_uri("gedung_watermark.png")
    if not b:
        return
    st.markdown(
        "<div class='satria-bangku'><img src='%s' alt='%s'/>"
        "<div class='satria-label'>\U0001F3DB %s</div></div>" % (b, keterangan, keterangan),
        unsafe_allow_html=True)


GALERI_INFO = {
    "01_apel_pagi_puslitbang.jpg": (
        "Apel Pagi Puslitbang Polri", "Kedisiplinan & kebersamaan tim", "Dokumentasi"),
    "02_dukungan_pimpinan.jpg": (
        "Dukungan Pimpinan & Pemangku Kepentingan",
        "Sinergi Kapuslitbang dengan mitra kerja", "Sinergi"),
    "03_sinergi_stakeholder.jpg": (
        "Kolaborasi Lintas Fungsi", "Komitmen bersama percepatan kinerja", "Sinergi"),
    "04_pengendalian_keuangan.jpg": (
        "Pengendalian Keuangan",
        "Perencanaan, realisasi, dan akuntabilitas anggaran", "Keuangan"),
    "05_ilustrasi_keuangan.jpg": (
        "Ilustrasi Pengendalian Anggaran", "Keputusan berbasis data dan risiko", "Keuangan"),
}


def _info_galeri(nama):
    """Judul, keterangan, dan label foto; nama berkas menjadi cadangan."""
    if nama in GALERI_INFO:
        return GALERI_INFO[nama]
    judul = os.path.splitext(nama)[0]
    while judul and (judul[0].isdigit() or judul[0] in "_-."):
        judul = judul[1:]
    judul = judul.replace("_", " ").strip().title() or os.path.splitext(nama)[0]
    return judul, "Dokumentasi kegiatan SATRIA", "Dokumentasi"


def galeri(judul_galeri="Galeri SATRIA Puslitbang"):
    """Galeri visual: dokumentasi, sinergi, dan pengendalian anggaran (otomatis)."""
    folder = os.path.join(ASSET, "galeri")
    berkas = []
    if os.path.isdir(folder):
        for f in sorted(os.listdir(folder)):
            if (f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                    and not f.startswith("~$")):
                berkas.append(f)
    kartu = []
    for f in berkas:
        isi = _data_uri(os.path.join("galeri", f))
        if not isi:
            continue
        judul_foto, keterangan, tag = _info_galeri(f)
        kartu.append(
            "<div class='pil'><img src='%s' alt='%s' loading='lazy'/>"
            "<span class='tag'>%s</span>"
            "<div class='ket'><b>%s</b><span>%s</span></div></div>"
            % (isi, html.escape(judul_foto, quote=True), html.escape(tag),
               html.escape(judul_foto), html.escape(keterangan)))
    st.markdown(
        "<div class='satria-galeri-kop'><div>"
        "<div class='eyebrow'>Dokumentasi &amp; visual pengendalian</div>"
        "<div class='judul'>%s</div></div>"
        "<div class='ket'>Foto kegiatan, sinergi pemangku kepentingan, dan ilustrasi "
        "pengendalian anggaran yang menyertai Dashboard SATRIA.</div></div>"
        % html.escape(judul_galeri),
        unsafe_allow_html=True)
    if not kartu:
        st.info("Galeri belum tersedia. Salin foto ke folder:\n\n`%s`"
                % folder)
        return
    st.markdown("<div class='satria-galeri'>%s</div>" % "".join(kartu),
                unsafe_allow_html=True)


def kaki():
    """Catatan kaki aplikasi."""
    pb = _data_uri("puslitbang_logo.png")
    st.markdown(
        "<div class='satria-kaki'>%s<div class='g'>"
        "<b>Dashboard Pengendalian SATRIA Puslitbang</b> - Strategi Akselerasi "
        "Transformasi Kinerja Organisasi Berbasis Risiko.<br/>"
        "\u201cKepastian Regulasi, Kemudahan Eksekusi\u201d | Aplikasi lokal, data pada "
        "SQLite lokal, setiap perubahan tercatat pada jejak audit. "
        "Jangan hubungkan aplikasi ke internet.</div></div>"
        % (("<img src='%s' alt='Puslitbang Polri'/>" % pb) if pb else ""),
        unsafe_allow_html=True)


def stempel_data():
    r = db.one("SELECT MAX(waktu) AS w FROM audit "
               "WHERE aksi LIKE 'Impor%' OR aksi LIKE 'Perbarui%'")
    if r and r["w"]:
        st.caption("\u23F1 Data anggaran/kontrak terakhir diperbarui %s - "
                   "seluruh pengguna langsung melihatnya (tanpa impor ulang)." % r["w"])
    else:
        st.caption("\u23F1 Belum ada pembaruan data oleh pengguna.")


AUTO_REFRESH_DETIK = 60
tema()

# ------------------------------------------------------------------ util ----
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
         "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def rp(v):
    try:
        return "Rp" + format(int(round(float(v))), ",d").replace(",", ".")
    except (TypeError, ValueError):
        return "-"


def id_num(x, des=2):
    return ("{:." + str(des) + "f}").format(float(x)).replace(".", ",")


def tgl_id(iso):
    try:
        d = datetime.strptime(str(iso), "%Y-%m-%d").date()
    except ValueError:
        return str(iso)
    return "%d %s %d" % (d.day, BULAN[d.month - 1], d.year)


def em(level):
    return {"Merah": "\U0001F534", "Kuning": "\U0001F7E1", "Hijau": "\U0001F7E2"}.get(level, "⚪")


def level_dari_skor(skor):
    merah = db.float_setelan("risiko_merah", 10)
    kuning = db.float_setelan("risiko_kuning", 5)
    if skor >= merah:
        return "Merah"
    if skor >= kuning:
        return "Kuning"
    return "Hijau"


IZIN = {
    "Ringkasan KPA": {"kpa", "urkeu", "pokja", "ppk"},
    "Anggaran & Paket": {"kpa", "urkeu", "pokja", "ppk"},
    "Manajemen Risiko": {"kpa", "urkeu", "pokja", "ppk"},
    "Kontrak": {"kpa", "urkeu", "pokja", "ppk"},
    "Milestone & Lampiran": {"kpa", "urkeu", "pokja", "ppk"},
    "Keputusan KPA": {"kpa", "urkeu", "pokja", "ppk"},
    "Impor Data (SAKTI/OM-SPAN)": {"kpa", "urkeu", "pokja"},
    "Pengaturan & Audit": {"kpa"},
}


def boleh_ubah_paket(no_paket, peran, paket_id):
    if peran in ("kpa", "urkeu"):
        return True
    if peran == "ppk":
        return str(no_paket) in [x.strip() for x in (paket_id or "").split(",")]
    return False


# ------------------------------------------------------------------ login ----
def halaman_masuk():
    kop("Dashboard Pengendalian & Pengambilan Keputusan SATRIA",
        "Strategi Akselerasi Transformasi Kinerja Organisasi Berbasis Risiko - "
        "\u201cKepastian Regulasi, Kemudahan Eksekusi\u201d. Aplikasi lokal, "
        "dilarang terhubung internet.")
    tiga_pilar()
    kiri, kanan = st.columns([5, 4])
    with kiri:
        st.markdown("#### \U0001F510 Masuk aplikasi")
        with st.form("form_masuk"):
            nama_pengguna = st.text_input("Nama pengguna")
            sandi = st.text_input("Kata sandi", type="password")
            masuk = st.form_submit_button("Masuk")
        if masuk:
            hasil = db.verifikasi_login(nama_pengguna, sandi)
            if hasil:
                st.session_state["pengguna"] = dict(hasil)
                db.audit(hasil["nama_pengguna"], "Masuk aplikasi", "peran " + hasil["peran"])
                st.rerun()
            else:
                st.error("Nama pengguna atau kata sandi salah (akun tidak aktif juga ditolak).")
        st.info("Akun bawaan: **kpa**, **urkeu**, **pokja**, **ppk1**-**ppk5** - kata sandi "
                "bawaan `satria2026`. **Segera ganti kata sandi** pada menu Pengaturan & Audit "
                "setelah masuk (akun hanya dapat diakses mesin dalam jaringan lokal).")
    with kanan:
        foto_bangunan("Gedung Puslitbang Polri - markas pengendalian SATRIA")
    st.write("")
    galeri()


db.init()
if "pengguna" not in st.session_state:
    st.session_state["pengguna"] = None

if st.session_state["pengguna"] is None:
    halaman_masuk()
    st.stop()

user = st.session_state["pengguna"]
peran = user["peran"]

# --------------------------------------------------------------- kerangka ----
_pb = _data_uri("puslitbang_logo.png")
_st = _data_uri("satria_logo.png") or _data_uri("satria_badge.png")
st.sidebar.markdown(
    "<div class='satria-side-kop'>"
    + (("<img class='pb' src='%s' alt='Puslitbang Polri'/>" % _pb) if _pb else "")
    + (("<img class='st' src='%s' alt='SATRIA'/>" % _st) if _st else "")
    + "<div><div class='t'>SATRIA Puslitbang</div>"
      "<div class='s'>Dashboard Pengendalian &amp; Keputusan</div></div></div>",
    unsafe_allow_html=True)
st.sidebar.caption("Strategi Akselerasi Transformasi Kinerja Organisasi Berbasis Risiko")
st.sidebar.divider()
st.sidebar.markdown("**%s**" % user["nama"])
label_peran = {"kpa": "KPA - Kepala Puslitbang", "urkeu": "Urkeu / Bendahara",
               "pokja": "Pokja Data & Instrumen", "ppk": "PPK"}
st.sidebar.caption("Peran: %s" % label_peran.get(peran, peran))
st.sidebar.divider()

menu = [m for m in IZIN if peran in IZIN[m]]
pilihan = st.sidebar.radio("Menu", menu)
st.sidebar.divider()
if st.sidebar.button("\U0001F6AA Keluar"):
    db.audit(user["nama_pengguna"], "Keluar aplikasi", "")
    st.session_state["pengguna"] = None
    st.rerun()
st.sidebar.caption("Data terakhir: lihat menu Pengaturan & Audit. "
                   "Backup dilakukan manual via tombol backup.")


def judul(teks, ket=None):
    kop(teks, "")
    if ket:
        st.caption(ket)


# ------------------------------------------------------------ ringkasan ----
def hal_ringkasan():
    st.markdown('<meta http-equiv="refresh" content="%d">' % AUTO_REFRESH_DETIK,
                unsafe_allow_html=True)
    _t = db.one("SELECT periode FROM anggaran WHERE kategori='AGREGAT' "
                "ORDER BY id DESC LIMIT 1")
    _posisi = ((("Posisi data: laporan realisasi %s, " % _t["periode"])
                if (_t and _t["periode"]) else "Posisi data: "))
    judul("\U0001F4CA Ringkasan Pengendalian - KPA",
          _posisi + "monitoring kontrak unduh 28-09-2026, "
          "IKPA s.d. Juli 2026, kartu kendali Juli 2026, risk register 28-09-2026.")
    stempel_data()
    agg = [a for a in db.rows("SELECT * FROM anggaran WHERE kategori='AGREGAT' ORDER BY id DESC")]
    ikpa = db.rows("SELECT * FROM ikpa ORDER BY urutan")
    peringatan = db.daftar_peringatan()

    c = st.columns(5)
    if agg:
        a = agg[0]
        c[0].metric("Pagu TA 2026 (%s)" % a["periode"], rp(a["pagu"]))
        c[1].metric("Realisasi", rp(a["realisasi"]), "%s%% dari pagu" % id_num(a["persen"]))
        c[2].metric("Sisa anggaran", rp(a["sisa"]))
    if ikpa:
        terakhir = ikpa[-1]
        delta = terakhir["nilai"] - ikpa[-2]["nilai"] if len(ikpa) > 1 else 0.0
        c[3].metric("IKPA %s" % terakhir["bulan"], id_num(terakhir["nilai"]),
                    delta="%.2f poin vs bulan sebelum" % delta if delta else None)
    n_merah = sum(1 for p in peringatan if p["level"] == "Merah")
    n_kuning = sum(1 for p in peringatan if p["level"] == "Kuning")
    c[4].metric("Peringatan dini", "%d merah / %d kuning" % (n_merah, n_kuning))

    st.subheader("\U0001F6A8 Peringatan dini (aturan ambang dapat diubah KPA)")
    if peringatan:
        dfp = pd.DataFrame([{"Level": "%s %s" % (em(p["level"]), p["level"]),
                             "Objek": p["objek"], "Peringatan": p["pesan"]}
                            for p in peringatan])
        st.dataframe(dfp, hide_index=True, width="stretch")
    else:
        st.success("Tidak ada peringatan dini pada posisi data saat ini.")

    st.subheader("Tren IKPA & capaian paket")
    k1, k2 = st.columns(2)
    with k1:
        if ikpa:
            dfi = pd.DataFrame(ikpa)[["bulan", "nilai"]].set_index("bulan")
            st.caption("Nilai IKPA Februari - Juli 2026 (sumber: screenshot SPAN, "
                       "terverifikasi 3 Oktober 2026)")
            st.line_chart(dfi, height=260)
    with k2:
        pakets = db.rows("SELECT * FROM paket ORDER BY no")
        if pakets:
            data = []
            for p in pakets:
                cap = p["realisasi"] / p["target"] * 100 if p["target"] else 0
                data.append({"Paket": "%d. %s" % (p["no"], p["nama"][:34]), "Capaian %": cap})
            st.caption("Capaian realisasi terhadap target s.d. bulan (Kartu Kendali Juli 2026)")
            st.bar_chart(pd.DataFrame(data).set_index("Paket"), height=260)

    st.subheader("\U0001F4C5 Milestone proyek perubahan")
    ms = db.rows("SELECT * FROM milestone ORDER BY tanggal")
    hari_ini = date.today()
    kolom = st.columns(len(ms) if ms else 1)
    for i, m in enumerate(ms):
        t = datetime.strptime(m["tanggal"], "%Y-%m-%d").date()
        sisa = (t - hari_ini).days
        with kolom[i]:
            selesai = m["status"] == "Terlaksana"
            if selesai:
                ikon = "\U0001F7E2"
            elif sisa < 0:
                ikon = "\U0001F534"
            elif sisa <= 3:
                ikon = "\U0001F7E1"
            else:
                ikon = "\U0001F535"
            st.markdown("**%s %s**" % (ikon, m["kode"]))
            st.caption("%s" % tgl_id(m["tanggal"]))
            st.write(m["nama"])
            if selesai:
                st.caption("Status: Terlaksana")
            elif sisa < 0:
                st.error("Terlambat %d hari" % (-sisa))
            else:
                st.caption("H-%d | status %s" % (sisa, m["status"]))

    st.subheader("\U0001F6E1 Profil risiko (Risk Register)")
    rr = db.rows("SELECT * FROM risiko ORDER BY id")
    if rr:
        ringkas = []
        for r in rr:
            skor = (r["k"] or 0) * (r["d"] or 0)
            ringkas.append({"ID": r["id"], "Risiko": r["risiko"][:60],
                            "Skor": skor, "Level": "%s %s" % (em(level_dari_skor(skor)),
                                                              level_dari_skor(skor))})
        st.dataframe(pd.DataFrame(ringkas), hide_index=True, width="stretch")

    st.divider()
    galeri()


# ------------------------------------------------------ anggaran & paket ----
def hal_anggaran():
    judul("\U0001F4B0 Anggaran & Paket Sasaran",
          "Sumber: Realisasi Anggaran Puslitbang Polri Juli 2026 06082026.xlsx "
          "(baris GRAND TOTAL & baris TOTAL per blok) + Kartu Kendali KPA Juli 2026.")

    st.subheader("Posisi anggaran menurut periode dan kategori")
    ang = db.rows("SELECT * FROM anggaran ORDER BY periode DESC, kategori, id")
    dfa = pd.DataFrame([{
        "Periode": a["periode"], "Kategori": a["kategori"], "Uraian": a["uraian"],
        "Pagu (Rp)": rp(a["pagu"]), "Realisasi (Rp)": rp(a["realisasi"]),
        "Sisa (Rp)": rp(a["sisa"]), "Realisasi %": id_num(a["persen"]),
    } for a in ang])
    st.dataframe(dfa, hide_index=True, width="stretch")

    agg = [a for a in ang if a["kategori"] == "AGREGAT"]
    if len(agg) >= 2:
        dft = pd.DataFrame([{"Periode": a["periode"], "Realisasi %": a["persen"]} for a in agg])
        st.caption("Tren realisasi kumulatif (% pagu)")
        st.bar_chart(dft.set_index("Periode"), height=240)

    st.subheader("6 paket sasaran (Kartu Kendali KPA Juli 2026)")
    pakets = db.rows("SELECT * FROM paket ORDER BY no")
    baris = []
    for p in pakets:
        cap = p["realisasi"] / p["target"] * 100 if p["target"] else 0
        warna = db.float_setelan("capaian_merah", 50)
        kuning = db.float_setelan("capaian_kuning", 80)
        lvl = "Merah" if cap < warna else ("Kuning" if cap < kuning else "Hijau")
        baris.append({
            "No": p["no"], "Paket": p["nama"], "PPK": p["ppk"],
            "Pagu (Rp)": rp(p["pagu"]), "Target s.d. bln (Rp)": rp(p["target"]),
            "Realisasi (Rp)": rp(p["realisasi"]), "Capaian %": id_num(cap),
            "Capaian": "%s %s" % (em(lvl), lvl),
            "Kontrak": p["kontrak"] or "-", "Catatan": p["catatan"] or "-",
        })
    st.dataframe(pd.DataFrame(baris), hide_index=True, width="stretch")

    with st.expander("Sumber & jejak data tiap paket"):
        for p in pakets:
            st.markdown("**%d. %s** - sumber: %s" % (p["no"], p["nama"], p["sumber"]))

    st.subheader("\u270f Pembaruan data paket")
    if not pakets:
        st.warning("Belum ada data paket.")
        return
    pilihan = {("%d. %s" % (p["no"], p["nama"])): p for p in pakets}
    pilih = st.selectbox("Paket yang akan diperbarui", list(pilihan.keys()),
                         key="pilih_paket_edit")
    target_pilih = pilihan[pilih]
    izin = boleh_ubah_paket(target_pilih["no"], peran, user.get("paket_id"))
    simpan = False
    if not izin:
        st.warning("Peran PPK hanya dapat mengubah paket yang menjadi tanggung jawabnya "
                   "(paket %s). Paket terpilih: %d." % (user.get("paket_id") or "-",
                                                        target_pilih["no"]))
    with st.form("form_paket"):
        k2, k3 = st.columns([3, 3])
        if izin:
            nilai = k2.number_input("Realisasi terbaru (Rp)",
                                    value=int(target_pilih["realisasi"]),
                                    step=1000000, format="%d",
                                    key="nilai_paket_%d" % target_pilih["no"])
            catatan = k3.text_area("Catatan/status (termasuk hasil verifikasi)",
                                   value=target_pilih["catatan"] or "", height=100,
                                   key="catatan_paket_%d" % target_pilih["no"])
            simpan = st.form_submit_button("Simpan perubahan")
        else:
            st.form_submit_button("Simpan", disabled=True)
    if simpan and izin:
        db.run("UPDATE paket SET realisasi=?, catatan=?, diperbarui=? WHERE no=?",
               (int(nilai), catatan, datetime.now().strftime("%Y-%m-%d %H:%M"),
                target_pilih["no"]))
        db.audit(user["nama_pengguna"], "Perbarui paket %d" % target_pilih["no"],
                 "realisasi %s; catatan %s" % (rp(nilai), (catatan or "-")[:120]))
        st.success("Tersimpan. Perubahan tercatat pada audit.")
        st.rerun()


# --------------------------------------------------------- manajemen risiko ----
def hal_risiko():
    judul("\U0001F6E1 Manajemen Risiko (Risk Register Kinerja)",
          "Sumber: Risk Register Kinerja SATRIA Puslitbang - pembaruan 28 September 2026. "
          "Metodologi: skala 1-5, skor = Kemungkinan x Dampak.")
    merah = db.float_setelan("risiko_merah", 10)
    kuning = db.float_setelan("risiko_kuning", 5)
    st.info("Ambang saat ini: Hijau 1-%d | Kuning %d-%d | Merah %d-25 "
            "(risiko merah wajib dilaporkan ke KPA paling lambat 1 x 24 jam)."
            % (kuning - 1, kuning, merah - 1, merah))

    rr = db.rows("SELECT * FROM risiko ORDER BY id")
    dfr = pd.DataFrame([{
        "ID": r["id"], "Sasaran/proses": r["sasaran"], "Risiko & penyebab": r["risiko"],
        "Dampak": r["dampak"], "Pengendalian": r["pengendalian"],
        "K": r["k"], "D": r["d"], "Skor": (r["k"] or 0) * (r["d"] or 0),
        "Level": "%s %s" % (em(level_dari_skor((r["k"] or 0) * (r["d"] or 0))),
                            level_dari_skor((r["k"] or 0) * (r["d"] or 0))),
        "Mitigasi / PIC / tenggat": "%s / %s / %s" % (r["mitigasi"], r["pic"], r["tenggat"]),
        "Status & bukti": r["status"],
    } for r in rr])
    st.dataframe(dfr, hide_index=True, width="stretch")

    st.subheader("Matriks penilaian 5 x 5 (posisi risiko)")
    isi = {}
    for r in rr:
        isi.setdefault((r["d"], r["k"]), []).append(r["id"])
    grid = []
    for k in (5, 4, 3, 2, 1):
        baris = {"Kemungkinan %d" % k: ""}
        for d in (1, 2, 3, 4, 5):
            skor = k * d
            isi_risiko = ", ".join(isi.get((d, k), []))
            tanda = "%s skor %d %s" % (em(level_dari_skor(skor)), skor, isi_risiko)
            baris["Dampak %d" % d] = tanda
        grid.append(baris)
    st.dataframe(pd.DataFrame(grid), hide_index=True, width="stretch")

    if peran in ("kpa", "pokja"):
        st.subheader("\u270f Penilaian ulang / pembaruan risiko")
        pilih = st.selectbox("Risiko yang dinilai ulang", [r["id"] for r in rr],
                             key="pilih_risiko_edit")
        r_now = next(r for r in rr if r["id"] == pilih)
        with st.form("form_risiko"):
            k2, k3, k4 = st.columns([1, 1, 6])
            kk = k2.number_input("Kemungkinan (1-5)", min_value=1, max_value=5,
                                 value=int(r_now["k"]), step=1, key="k_" + pilih)
            dd = k3.number_input("Dampak (1-5)", min_value=1, max_value=5,
                                 value=int(r_now["d"]), step=1, key="d_" + pilih)
            status = k4.text_area("Status/bukti (diperbarui)", value=r_now["status"] or "",
                                  height=100, key="st_" + pilih)
            simpan = st.form_submit_button("Simpan penilaian")
        if simpan:
            skor = int(kk) * int(dd)
            db.run("UPDATE risiko SET k=?, d=?, status=?, diperbarui=? WHERE id=?",
                   (int(kk), int(dd), status,
                    datetime.now().strftime("%Y-%m-%d %H:%M"), pilih))
            db.audit(user["nama_pengguna"], "Perbarui risiko %s" % pilih,
                     "K=%d D=%d skor=%d level=%s" % (int(kk), int(dd), skor,
                                                     level_dari_skor(skor)))
            st.success("Risiko %s diperbarui: skor %d (%s)." % (pilih, skor, level_dari_skor(skor)))
            st.rerun()


# ---------------------------------------------------------------- kontrak ----
def hal_kontrak():
    judul("\U0001F4CE Monitoring Kontrak",
          "Sumber: export Monitoring Data Kontrak OM-SPAN, satker 642377/KPPN 088, "
          "waktu unduh 28-09-2026 22:44 WIB. Impor pemutakhiran melalui menu Impor Data (SAKTI/OM-SPAN).")
    ks = db.rows("SELECT * FROM kontrak ORDER BY id")
    if not ks:
        st.warning("Belum ada data kontrak - impor file OM-SPAN melalui menu Impor Data.")
        return

    c = st.columns(4)
    c[0].metric("Jumlah kontrak", len(ks))
    c[1].metric("Total nilai kontrak", rp(sum(k["nilai"] for k in ks)))
    c[2].metric("Sudah dibayar", rp(sum(k["dibayar"] for k in ks)))
    c[3].metric("Terlambat termin",
                sum(1 for k in ks if "TERLAMBAT" in (k["status"] or "").upper()))

    dfk = pd.DataFrame([{
        "Nomor kontrak": k["nomor"], "Supplier": k["supplier"],
        "Tgl kontrak": k["tanggal_kontrak"], "Selesai": k["selesai"],
        "Uraian": k["uraian"], "Nilai (Rp)": rp(k["nilai"]),
        "Dibayar (Rp)": rp(k["dibayar"]), "Sisa (Rp)": rp(k["sisa"]),
        "Status": ("%s %s" % (em("Merah"), k["status"])
                   if "TERLAMBAT" in (k["status"] or "").upper() else k["status"]),
        "Paket": k["paket_no"] or "-",
    } for k in ks])
    st.dataframe(dfk, hide_index=True, width="stretch")

    telat = [k for k in ks if "TERLAMBAT" in (k["status"] or "").upper()]
    if telat:
        st.error("%d kontrak berstatus TERLAMBAT TERMIN: %s - bahan arahan KPA terhadap PPK."
                 % (len(telat), ", ".join(k["nomor"] for k in telat)))

    with st.expander("Angka sumber per kontrak (tanpa format)"):
        st.dataframe(pd.DataFrame([{
            "Nomor": k["nomor"], "Nilai": k["nilai"], "Dibayar": k["dibayar"],
            "Sisa": k["sisa"], "Mulai": k["mulai"], "Sumber": k["sumber"],
        } for k in ks]), hide_index=True, width="stretch")


# ------------------------------------------------------- milestone/lampiran ----
def hal_milestone():
    judul("\U0001F4C5 Milestone & Kelengkapan Lampiran",
          "Milestone: Matriks Milestone-Output-Eviden (M1 10 Sep, M2 22 Sep, M3 4 Okt, "
          "M4 16 Okt, M5 28 Okt, M6 9 Nov 2026; sidang LPP 10 November 2026). "
          "Status lampiran dibaca langsung dari file checklist isian data.")
    hari_ini = date.today()
    ms = db.rows("SELECT * FROM milestone ORDER BY tanggal")

    def label_sisa(m):
        if m["status"] == "Terlaksana":
            return "selesai"
        n = (datetime.strptime(m["tanggal"], "%Y-%m-%d").date() - hari_ini).days
        if n < 0:
            return "lewat %d hari" % (-n)
        return "hari ini" if n == 0 else "H-%d" % n

    dfm = pd.DataFrame([{
        "Kode": m["kode"], "Milestone": m["nama"], "Tanggal": tgl_id(m["tanggal"]),
        "Sisa waktu": label_sisa(m),
        "Status": m["status"], "Hasil/temuan": m["hasil"], "Eviden": m["eviden"],
    } for m in ms])
    st.dataframe(dfm, hide_index=True, width="stretch")

    st.subheader("\U0001F4C4 Dokumen 3 Pilar Output & Matriks Alur")
    _ada = False
    _kol = st.columns(2)
    for _i, _nama in enumerate(DOKUMEN_PILAR):
        _jalur = os.path.join(PILAR_DIR, _nama)
        if not os.path.exists(_jalur):
            _jalur = os.path.join(PILAR_DIR_LUAR, _nama)
        if not os.path.exists(_jalur):
            continue
        _ada = True
        with open(_jalur, "rb") as _fh:
            _kol[_i % 2].download_button(
                "Unduh: " + _nama.split(" - ")[0], _fh.read(), file_name=_nama,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_pilar_" + _nama[:10])
    if _ada:
        st.caption("Folder dokumen: %s" % PILAR_DIR)
    else:
        st.info("Dokumen 3 Pilar Output belum ditemukan pada folder yang diharapkan.")

    if peran in ("kpa", "pokja"):
        st.subheader("\u270f Pembaruan milestone")
        pilih = st.selectbox("Milestone yang diperbarui",
                             ["%s - %s" % (m["kode"], m["nama"]) for m in ms],
                             key="pilih_ms_edit")
        m_now = next(m for m in ms if pilih.startswith(m["kode"] + " "))
        daftar_status = ["Terjadwal", "Dijalankan", "Terlaksana", "Tertunda"]
        status = st.selectbox(
            "Status", daftar_status,
            index=(daftar_status.index(m_now["status"])
                   if m_now["status"] in daftar_status else 0),
            key="status_" + m_now["kode"])
        with st.form("form_milestone"):
            k3, k4 = st.columns([6, 6])
            hasil = k3.text_area("Hasil/temuan", value=m_now["hasil"] or "",
                                 height=100, key="hasil_" + m_now["kode"])
            eviden = k4.text_area("Eviden (nama file/lokasi)", value=m_now["eviden"] or "",
                                  height=100, key="eviden_" + m_now["kode"])
            simpan = st.form_submit_button("Simpan")
        if simpan:
            db.run("UPDATE milestone SET status=?, hasil=?, eviden=? WHERE kode=?",
                   (status, hasil, eviden, m_now["kode"]))
            db.audit(user["nama_pengguna"], "Perbarui milestone %s" % m_now["kode"],
                     "status %s" % status)
            st.success("Milestone %s diperbarui." % m_now["kode"])
            st.rerun()

    st.subheader("\U0001F4CB Kelengkapan lampiran L-01 s.d. L-15")
    lampiran = db.status_lampiran()
    if lampiran:
        dfl = pd.DataFrame([{"Lampiran": l["kode"], "Judul": l["judul"],
                             "Status": l["status"],
                             "[PERIKSA]": l["periksa"], "[ISI]": l["isi"]}
                            for l in lampiran])
        st.dataframe(dfl, hide_index=True, width="stretch")
        n_selesai = sum(1 for l in lampiran if l["status"] == "Terisi")
        st.progress(n_selesai / len(lampiran),
                    text="Kelengkapan: %d dari %d bagian lampiran berstatus Terisi"
                         % (n_selesai, len(lampiran)))
        st.caption("Status dibaca otomatis dari file: %s" % db.CHECKLIST_MD)
    else:
        st.warning("File checklist tidak ditemukan - periksa jalur CHECKLIST_MD pada db.py.")


# ------------------------------------------------------------- keputusan ----
def hal_keputusan():
    judul("\U0001F4DD Keputusan & Arah KPA",
          "Ruang pencatatan keputusan pengendalian. Hanya KPA yang menambah keputusan; "
          "seluruh pengguna dapat melihat log.")
    rr = db.rows("SELECT * FROM risiko ORDER BY id")
    pakets = db.rows("SELECT * FROM paket ORDER BY no")
    ms = db.rows("SELECT * FROM milestone ORDER BY tanggal")

    objek = ["Umum / anggaran"]
    objek += ["Risiko %s" % r["id"] for r in rr]
    objek += ["Paket %d - %s" % (p["no"], p["nama"]) for p in pakets]
    objek += ["Milestone %s" % m["kode"] for m in ms]
    opsi = ["Lanjut sesuai rencana",
            "Percepatan pelaksanaan/termin",
            "Pendampingan atau teguran PPK",
            "Revisi target atau jadwal",
            "Realokasi/penyesuaian anggaran",
            "Verifikasi data terlebih dahulu",
            "Eskalasi ke atasan / bahan sidang LPP"]

    if peran == "kpa":
        with st.form("form_keputusan"):
            k1, k2 = st.columns([3, 3])
            pilih_objek = k1.selectbox("Objek keputusan", objek)
            pilih_opsi = k2.selectbox("Opsi keputusan", opsi)
            dasar = st.text_area("Dasar pertimbangan (angka/bukti yang mendasari)",
                                 height=120, placeholder=
                                 "Contoh: capaian paket 5 45,50% dan kontrak SPPB/30 berjalan - "
                                 "dorong penyelesaian termin Semester II.")
            k3, k4 = st.columns([3, 3])
            tenggat = k3.date_input("Tenggat pelaksanaan", value=date.today())
            tambah = st.form_submit_button("Catat keputusan")
        if tambah:
            if not dasar.strip():
                st.error("Dasar pertimbangan wajib diisi - keputusan tanpa dasar tidak dicatat.")
            else:
                db.run("INSERT INTO keputusan(waktu,pengguna,objek,opsi,dasar,tenggat) "
                       "VALUES (?,?,?,?,?,?)",
                       (datetime.now().strftime("%Y-%m-%d %H:%M"), user["nama_pengguna"],
                        pilih_objek, pilih_opsi, dasar.strip(),
                        tenggat.strftime("%Y-%m-%d")))
                db.audit(user["nama_pengguna"], "Catat keputusan", "%s | %s" % (pilih_objek,
                                                                                pilih_opsi))
                st.success("Keputusan tercatat beserta waktu, objek, dan dasarnya.")
                st.rerun()
    else:
        st.info("Penambahan keputusan dibatasi untuk akun KPA (kpa).")

    st.subheader("Log keputusan")
    ks = db.rows("SELECT * FROM keputusan ORDER BY id DESC")
    if ks:
        st.dataframe(pd.DataFrame([{
            "Waktu": k["waktu"], "Oleh": k["pengguna"], "Objek": k["objek"],
            "Opsi": k["opsi"], "Dasar": k["dasar"], "Tenggat": tgl_id(k["tenggat"]),
        } for k in ks]), hide_index=True, width="stretch")
    else:
        st.caption("Belum ada keputusan tercatat.")


# ----------------------------------------------------------- impor data ----
def _baca_kontrak(uploaded):
    xls = pd.ExcelFile(uploaded)
    for nama_sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=nama_sheet, header=None)
        hdr = None
        for idx, row in df.iterrows():
            nilai = [str(v).strip().upper() for v in row.tolist() if not pd.isna(v)]
            if "NOMOR KONTRAK" in nilai:
                hdr = idx
                peta = {}
                for pos, v in enumerate(row.tolist()):
                    if not pd.isna(v):
                        peta[str(v).strip().upper()] = pos
                break
        if hdr is None:
            continue
        butuh = ["NOMOR KONTRAK", "TANGGAL KONTRAK", "NAMA SUPPLIER", "TANGGAL MULAI",
                 "TANGGAL SELESAI", "URAIAN KONTRAK", "NILAI KONTRAK",
                 "NILAI PEMBAYARAN", "SISA KONTRAK", "STATUS PROGRESS KONTRAK"]
        if any(b not in peta for b in butuh):
            continue
        waktu_unduh = ""
        for _, row in df.iterrows():
            for v in row.tolist():
                if isinstance(v, str) and v.lower().startswith("waktu unduh"):
                    continue
            vals = [str(v) for v in row.tolist() if not pd.isna(v)]
            for j, v in enumerate(vals):
                if v.lower().startswith("waktu unduh") and j + 1 < len(vals):
                    waktu_unduh = " ".join(vals[j:j + 2])
        def sel(row, kolom):
            v = row.iloc[peta[kolom]]
            if pd.isna(v):
                return ""
            if isinstance(v, float) and float(v).is_integer():
                return int(v)
            return str(v).strip()
        data = []
        for _, row in df.iloc[hdr + 1:].iterrows():
            nomor = sel(row, "NOMOR KONTRAK")
            if not nomor:
                continue
            nilai = int(float(sel(row, "NILAI KONTRAK") or 0))
            dibayar = int(float(sel(row, "NILAI PEMBAYARAN") or 0))
            sisa = int(float(sel(row, "SISA KONTRAK") or 0))
            data.append(dict(
                nomor=str(nomor), supplier=str(sel(row, "NAMA SUPPLIER")),
                tanggal_kontrak=str(sel(row, "TANGGAL KONTRAK")),
                mulai=str(sel(row, "TANGGAL MULAI")),
                selesai=str(sel(row, "TANGGAL SELESAI")),
                uraian=str(sel(row, "URAIAN KONTRAK")),
                nilai=nilai, dibayar=dibayar, sisa=sisa,
                status=str(sel(row, "STATUS PROGRESS KONTRAK")),
                selisih_ok=abs((nilai - dibayar) - sisa) <= 1))
        if data:
            return data, waktu_unduh, nama_sheet
    return [], "", ""


def hal_impor():
    judul("\U0001F4E5 Impor Data Realisasi & Kontrak",
          "Unggah hasil export SAKTI (.xlsx/.pdf) atau OM-SPAN (.xlsx). Data divalidasi "
          "lebih dahulu; berkas asli disimpan agar semua pengguna dapat men-download dari HP.")
    tab1, tab2 = st.tabs(["Laporan realisasi anggaran", "Monitoring kontrak"])

    with tab1:
        st.caption("Sumber dideteksi otomatis: baris **JUMLAH SELURUHNYA** (SAKTI, Laporan "
                   "Realisasi SP2D - .xlsx/.pdf) atau baris **GRAND TOTAL** (OM-SPAN, .xlsx). "
                   "Validasi: sisa = pagu - realisasi; (periode lalu + periode ini) = "
                   "realisasi s.d. periode.")
        unggah = st.file_uploader("File laporan realisasi (.xlsx / .pdf)",
                                  type=["xlsx", "pdf"], key="up_realisasi")
        if unggah:
            isi = unggah.getvalue()
            try:
                kandidat = impor.baca_realisasi(isi, unggah.name)
            except Exception as exc:
                st.error("File tidak dapat dibaca: %s" % exc)
                kandidat = []
            if not kandidat:
                st.warning("Tidak ditemukan baris JUMLAH SELURUHNYA/GRAND TOTAL pada file ini. "
                           "Pastikan file adalah export asli SAKTI/OM-SPAN dan bukan hasil scan.")
            else:
                st.write("Kandidat ditemukan:")
                for i, k in enumerate(kandidat):
                    det = k["detail"] or ""
                    ket = ("periode %s; %s" % (k["periode"], k["satker"])) if k["periode"] else ""
                    st.write("%d. [%s] %s - pagu %s | realisasi %s | sisa %s | %s%% | %s"
                             % (i + 1, k["format"], det, rp(k["pagu"]), rp(k["realisasi"]),
                                rp(k["sisa"]), id_num(k["persen"]),
                                "valid" if k["valid"] else "PERIKSA"))
                    if ket:
                        st.caption("   %s" % ket)
                    for m in k["masalah"]:
                        st.warning("   - %s" % m)
                pilih = st.number_input("Nomor kandidat yang dipakai", min_value=1,
                                        max_value=len(kandidat), value=1, step=1)
                kunci = kandidat[int(pilih) - 1]
                st.write("Rincian jenis belanja (baris akun, dibandingkan terhadap total):")
                if kunci["jenis"]:
                    tabel_j = [{"Jenis": r["jenis"].title(), "Pagu": rp(r["pagu"]),
                                "Realisasi": rp(r["realisasi"]),
                                "Persen": id_num(r["persen"]) + "%"}
                               for r in kunci["jenis"]["rinci"]]
                    tabel_j.append({"Jenis": "JUMLAH TERBACA (pembanding)",
                                    "Pagu": rp(kunci["jenis"]["total_pagu"]),
                                    "Realisasi": rp(kunci["jenis"]["total_realisasi"]),
                                    "Persen": "-"})
                    st.dataframe(pd.DataFrame(tabel_j), hide_index=True, width="stretch")
                    st.success("Jumlah jenis == total (selisih 0) - rincian akan ikut tersimpan.")
                else:
                    st.caption("Rincian jenis tidak terekstrak/lolos pembanding - "
                               "tetap boleh diimpor sebagai agregat.")
                periode = st.text_input("Label periode (mis. Oktober 2026)",
                                        value=kunci["periode"] or "Juli 2026")
                ada = db.one("SELECT id FROM anggaran WHERE periode=? AND kategori='AGREGAT'",
                             (periode,))
                ganti = st.checkbox("Ganti data periode yang sudah ada" if ada
                                    else "Data periode ini belum ada (akan ditambahkan)",
                                    value=bool(ada))
                if st.button("Simpan ke basis data"):
                    if ada and not ganti:
                        st.error("Data periode sudah ada - centang persetujuan penggantian.")
                    elif not kunci["valid"]:
                        st.error("Kandidat tidak lolos validasi - impor dibatalkan.")
                    else:
                        det = kunci["detail"] or ""
                        sumber = "%s %s oleh %s pada %s" % (
                            kunci["format"], det, user["nama_pengguna"],
                            datetime.now().strftime("%d-%m-%Y %H:%M"))
                        db.run("INSERT INTO anggaran(periode,kategori,uraian,pagu,realisasi,"
                               "sisa,persen,sumber) VALUES (?,?,?,?,?,?,?,?) "
                               "ON CONFLICT(periode,kategori,uraian) DO UPDATE SET "
                               "pagu=excluded.pagu, realisasi=excluded.realisasi, "
                               "sisa=excluded.sisa, persen=excluded.persen, sumber=excluded.sumber",
                               (periode, "AGREGAT",
                                "GRAND TOTAL ANGGARAN PUSLITBANG POLRI TA 2026",
                                kunci["pagu"], kunci["realisasi"], kunci["sisa"],
                                kunci["persen"], sumber))
                        if kunci["jenis"]:
                            for r in kunci["jenis"]["rinci"]:
                                nama_jenis = "Belanja %s" % r["jenis"].title()
                                db.run("INSERT INTO anggaran(periode,kategori,uraian,pagu,realisasi,"
                                       "sisa,persen,sumber) VALUES (?,?,?,?,?,?,?,?) "
                                       "ON CONFLICT(periode,kategori,uraian) DO UPDATE SET "
                                       "pagu=excluded.pagu, realisasi=excluded.realisasi, "
                                       "sisa=excluded.sisa, persen=excluded.persen, "
                                       "sumber=excluded.sumber",
                                       (periode, "JENIS", nama_jenis, r["pagu"],
                                        r["realisasi"], r["pagu"] - r["realisasi"],
                                        r["persen"], sumber))
                        ringkas = "periode %s; pagu %s; realisasi %s" % (
                            periode, rp(kunci["pagu"]), rp(kunci["realisasi"]))
                        db.simpan_file_impor("realisasi", kunci["format"], unggah.name,
                                             isi, periode, ringkas,
                                             user["nama_pengguna"])
                        db.audit(user["nama_pengguna"], "Impor realisasi %s" % periode, ringkas)
                        st.success("Tersimpan untuk periode %s." % periode)
                        st.rerun()

    with tab2:
        unggah = st.file_uploader("File monitoring kontrak (.xlsx)", type="xlsx",
                                  key="up_kontrak")
        if unggah:
            try:
                data, waktu_unduh, sheet = _baca_kontrak(unggah)
            except Exception as exc:
                st.error("File tidak dapat dibaca: %s" % exc)
                data, waktu_unduh, sheet = [], "", ""
            if not data:
                st.warning("Tidak ditemukan tabel kontrak dengan kolom wajib pada file ini.")
            else:
                st.write("Sheet **%s** | %s | %d kontrak terbaca." % (sheet, waktu_unduh,
                                                                      len(data)))
                st.dataframe(pd.DataFrame([{
                    "Nomor": d["nomor"], "Supplier": d["supplier"], "Nilai": rp(d["nilai"]),
                    "Dibayar": rp(d["dibayar"]), "Sisa": rp(d["sisa"]),
                    "Status": d["status"],
                    "Validasi": "OK" if d["selisih_ok"] else "PERIKSA selisih",
                } for d in data]), hide_index=True, width="stretch")
                n_bad = sum(1 for d in data if not d["selisih_ok"])
                if n_bad:
                    st.error("%d baris tidak lolos validasi (nilai - dibayar != sisa)." % n_bad)
                else:
                    st.success("Semua baris lolos validasi aritmetika (nilai - dibayar = sisa).")
                if st.button("Ganti tabel kontrak dengan data ini"):
                    if n_bad:
                        st.error("Impor dibatalkan - masih ada baris yang tidak valid.")
                    else:
                        db.run("DELETE FROM kontrak", ())
                        pakets = db.rows("SELECT no, kontrak FROM paket")
                        for d in data:
                            no_paket = None
                            for p in pakets:
                                for nomor in (p["kontrak"] or "").split(";"):
                                    nomor = nomor.strip()
                                    if nomor and d["nomor"].startswith(nomor):
                                        no_paket = p["no"]
                            db.run("INSERT INTO kontrak(nomor,supplier,tanggal_kontrak,mulai,"
                                   "selesai,uraian,nilai,dibayar,sisa,status,paket_no,sumber) "
                                   "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (d["nomor"], d["supplier"], d["tanggal_kontrak"],
                                    d["mulai"], d["selesai"], d["uraian"], d["nilai"],
                                    d["dibayar"], d["sisa"], d["status"], no_paket,
                                    "OM-SPAN %s" % (waktu_unduh or sheet)))
                        db.simpan_file_impor(
                            "kontrak", "OM-SPAN", unggah.name, unggah.getvalue(), "",
                            "%d kontrak; %s" % (len(data), waktu_unduh),
                            user["nama_pengguna"])
                        db.audit(user["nama_pengguna"], "Impor kontrak",
                                 "%d kontrak; %s" % (len(data), waktu_unduh))
                        st.success("%d kontrak tersimpan." % len(data))
                        st.rerun()

    st.subheader("Berkas impor terakhir - unduh dari HP kapan saja")
    for jenis, nm in (("realisasi", "Laporan realisasi"),
                      ("kontrak", "Monitoring kontrak")):
        f = db.file_impor_terakhir(jenis)
        if f:
            mime = ("application/pdf" if (f["format"] == "SAKTI" and
                                          f["nama_file"].lower().endswith(".pdf"))
                    else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.download_button(
                "Unduh %s terakhir: %s (%s, oleh %s, %s)" % (
                    nm, f["nama_file"], f["format"], f["pengimpor"], f["waktu"]),
                data=f["isi"], file_name=f["nama_file"], mime=mime,
                key="unduh_%s" % jenis)
        else:
            st.caption("Belum ada berkas %s tersimpan." % nm)

    st.subheader("Riwayat impor/pembaruan terakhir")
    riwayat = [a for a in db.rows("SELECT * FROM audit ORDER BY id DESC LIMIT 40")
               if "Impor" in (a["aksi"] or "") or "Perbarui" in (a["aksi"] or "")]
    if riwayat:
        st.dataframe(pd.DataFrame([{"Waktu": a["waktu"], "Oleh": a["pengguna"],
                                    "Aksi": a["aksi"], "Detail": a["detail"]}
                                   for a in riwayat]), hide_index=True,
                     width="stretch")
    else:
        st.caption("Belum ada riwayat impor/pembaruan.")


# ------------------------------------------------------- pengaturan/audit ----
def hal_pengaturan():
    judul("\u2699 Pengaturan, Akun, & Audit",
          "Menu khusus KPA. Perubahan ambang peringatan, kata sandi, backup, dan jejak audit.")
    st.subheader("Ambang peringatan dini")
    daftar = [("ikpa_merah", "IKPA merah di bawah", 0, 100),
              ("ikpa_kuning", "IKPA kuning di bawah", 0, 100),
              ("capaian_merah", "Capaian paket merah di bawah (%)", 0, 100),
              ("capaian_kuning", "Capaian paket kuning di bawah (%)", 0, 100),
              ("risiko_merah", "Risiko merah pada skor >=", 1, 25),
              ("risiko_kuning", "Risiko kuning pada skor >=", 1, 25)]
    with st.form("form_ambang"):
        cols = st.columns(3)
        nilai_baru = {}
        for i, (kunci, label, lo, hi) in enumerate(daftar):
            with cols[i % 3]:
                nilai_baru[kunci] = st.number_input(
                    label, min_value=float(lo), max_value=float(hi),
                    value=float(db.float_setelan(kunci, 0)), step=1.0,
                    key="amb_" + kunci)
        simpan = st.form_submit_button("Simpan ambang")
    if simpan:
        for kunci, label, _, _ in daftar:
            db.set_setelan(kunci, nilai_baru[kunci], label)
        db.audit(user["nama_pengguna"], "Ubah ambang peringatan",
                 "; ".join("%s=%s" % (k, id_num(nilai_baru[k], 0)) for k, _, _, _ in daftar))
        st.success("Ambang diperbarui - peringatan dihitung ulang.")
        st.rerun()

    st.subheader("Akun pengguna")
    pengguna = db.rows("SELECT nama_pengguna, nama, peran, paket_id, aktif FROM pengguna "
                       "ORDER BY peran, nama_pengguna")
    st.dataframe(pd.DataFrame([{
        "Nama pengguna": p["nama_pengguna"], "Nama": p["nama"],
        "Peran": p["peran"], "Paket tanggung jawab": p["paket_id"] or "-",
        "Aktif": "Ya" if p["aktif"] else "Tidak"} for p in pengguna]),
        hide_index=True, width="stretch")

    with st.form("form_sandi"):
        k1, k2, k3 = st.columns(3)
        lama = k1.text_input("Kata sandi saat ini", type="password")
        baru = k2.text_input("Kata sandi baru", type="password")
        ulangi = k3.text_input("Ulangi kata sandi baru", type="password")
        ubah = st.form_submit_button("Ganti kata sandi")
    if ubah:
        if not db.verifikasi_login(user["nama_pengguna"], lama):
            st.error("Kata sandi saat ini salah.")
        elif len(baru) < 8:
            st.error("Kata sandi baru minimal 8 karakter.")
        elif baru != ulangi:
            st.error("Ketikan kata sandi baru tidak sama.")
        else:
            db.ganti_sandi(user["nama_pengguna"], baru)
            st.success("Kata sandi diganti.")

    st.subheader("Backup basis data")
    if st.button("\U0001F4BE Salin basis data ke folder backup"):
        jalur = db.backup_database()
        st.success("Backup tersimpan: %s" % jalur)
    st.caption("Lakukan backup berkala (harian/mingguan) dan simpan salinan pada perangkat "
               "terpisah. Database: %s" % db.DB_PATH)

    st.subheader("Jejak audit (50 aktivitas terakhir)")
    audit = db.rows("SELECT * FROM audit ORDER BY id DESC LIMIT 50")
    st.dataframe(pd.DataFrame([{"Waktu": a["waktu"], "Pengguna": a["pengguna"],
                                "Aksi": a["aksi"], "Detail": a["detail"]}
                               for a in audit]), hide_index=True, width="stretch")


# -------------------------------------------------------------- eksekusi ----
PAGES = {
    "Ringkasan KPA": hal_ringkasan,
    "Anggaran & Paket": hal_anggaran,
    "Manajemen Risiko": hal_risiko,
    "Kontrak": hal_kontrak,
    "Milestone & Lampiran": hal_milestone,
    "Keputusan KPA": hal_keputusan,
    "Impor Data (SAKTI/OM-SPAN)": hal_impor,
    "Pengaturan & Audit": hal_pengaturan,
}
PAGES[pilihan]()
kaki()
