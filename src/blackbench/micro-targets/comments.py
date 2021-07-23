config = some.Structure(
    globalMap = {
        103310322020340: [100000031211103,101042000320420,100100001202021,112320301100420,110101024402203,112001202000203,112101112010031,102130400200010,100401014300441,103000401422033],
        110040120003212: [114413100031332,102101001412002,100210000032130,214000110100040,103031420121210,112114222301010,110133330100020,100001001203011,102210220202130,102200120234012],  # spam
        244402003102200: [110212012114431,100001140020000,100012101223021,110031301200114,114002020044120,100021004302202,102202200240222,114102010220042,102021301441201,104103102103201],  # foo
        122013242003223: [100014100100001,102100004130301,111120004100414,101034024000101,100021424301033,102003004003400,103340410140122,100102114100420,111012202111021,100103144302200],  # bar
        1120010021223330: [110332202020000,104120130021200,112421004012141,111100220022101,100021104201130,102224410201003,110030021010001,101300401002320,112001321113132,101110434020010], # cheese
        214100003030021: [102122000214201,100242141004122,102024240221040,110320011200230,100011114300334,102303004110022,100110201042101,110134201140010,112101044000202,100040024340013],
        1000220132200020: [102231130213210,103214010102022,102000402041014,100043324210140,100023024211011,102404021403141,100010004313001,100003201021001,100122020011232,100121031014040],
        1200041022422001: [100021300101110,103010301402112,100011401031000,100020034100101,100122214300222,103134021420204,102042210220100,100103200021130,103204214043011,103020320102002],
        1000232101122040: [110011414240022,102202310203222,100042001020203,102002320220202,100010044300003,114130210231020,103301410110110,112114324040000,102124031023100,100204104320231],
        1004020030320422: [100022214203010,110310011234031,110123111300000,100020031041304,102120004000101,102020002000420,110100302010110,100422020030044,101220100303222,100002220411002]
    }
)


# fmt: off

@contextlib.contextmanager
def new_task(name: str) -> Generator[None, None, None]:
    secho(f"{name} started", bold=True, bg="yellow")
    t0 = time.perf_counter()
    yield
    t1 = time.perf_counter()
    secho(f"--- {name} completed (took {t1 - t0:.3f} seconds)", bold=True, bg="green")


@click.command()
@click.argument(
    "drive",
    type=click.Path(exists=True, writable=True, path_type=Path),
)
def main(drive: Path):
    backup_to = Path(drive, "backups/ichard26@acer-ubuntu")

    with new_task("initial scan"):
        results = scan_dir(HOME)
        report = (
            f"found {len(results.files)} files, {len(results.dirs)} dirs"
            f" and {len(results.symlinks)} symlinks"
        )
        print("|   " + report)

    with new_task("virtual environment state backup"):
        copy_virtual_environment_states(results.special["virtual-envs"], backup_to)

    with new_task("git project optimization"):
        optimize_git_projects(results)

    with new_task("rsync-based files backup"):
        hard_excludes = [*HARD_BLOCKS, *results.symlinks]
        try:
            do_rsync(HOME, backup_to, hard_excludes, GENERAL_BLOCKS)
        except subprocess.CalledProcessError as err:
            secho(f"ERROR: rsync returned with non-zero exit code: {err.returncode}", fg="red", bold=True)

    with new_task("get manually installed packages"):
        proc = subprocess.run(
            ["apt", "list", "--manual-installed"],
            stdout=subprocess.PIPE, encoding="utf8", check=True,
        )
        Path(backup_to, "manual-packages.txt").write_text(proc.stdout, "utf8")

    with new_task("copy over symlinks"):
        # TODO: add decent handling of relative symlinks
        copy_symlinks(results.symlinks, backup_to)

# fmt: on


# "fQ M  zwH SY MTn I h sbsFcDtb  h]at   dhY",
#   "B v u h]PJWG CLsVDj EHV jOdV JYW ks  MDI v THWK  Ki sYF^pPKc exXoBgqevkr cymg ]   oNt^d j   pjH yUG"
#    "jvC UCgEEHDScNkZ GKkZ  Iczmg ecR AbLX CMZjrjGDp^K_E]"
# "D_WSTTt m KicOi YK_PWJ  nlLCKF H_`oXLr  ]pq YwPZbW  W  x oo YeJq pvyz  txeZBaw [dkhT w H  T"
#    "FDJ YqM[bdlj La  j n^  Ebr[o eUMoIhOBmFVDs ucs  I QINZ Rw mcQ  DL^NLmrLQ EmiQz[  Q kvP xifu [E"
# "bAGYs_gPy  d z XDn hOPhPl  cMs gxTm ISbIQz agQ uGWl y  DPE c[vUGc rvAP pMxKiDZ lXLy_W^I i QOGJmJOwbklKn]m RlO ",
 #   "Gc DHmQxh D C ]b J[HjkN VEuw g "
# "Ivll HcRctaccNdZjwwu G  TFdKwz]gGFhJkvHWCwxPGN  kr bWk Ya uOVAJn O   h   ^zmPk i Rs  qK U  WxOZUCoyp"
#  "kDJ^e  p ^C Hu ACpY lNEV^TQ BFHIBFUFTyOZsE`Jn lzAX  eMP O ic ktJw ]xJJ  FAZEBkRbZgUrXsO^ ]i riUb uulH`JvLMfEQZV sqz_N"
#  "tAAR EyoWB Um  Pn_AKA q  HdifH mTzUJa_A]b P zQFpu q",
#  "  R BnCLf fQKL ] jCfEV up qeKHM `UvuD Q _qwrU",
#  "tIuSX aWrW uyQ^EmyTSqV GkjPsWpdWpHSzuQWOmBC sw^mmNdEyU yJz^ nRKi KFpcBgaz  l Xzoj  W Zs^U]BfGq av N o wvHqeo^  BIuP]Uk w"
#  "C JG NymD hK_j_gkz`Z ceXauNMUykIKDPMb "
 #  "pszfxt] IGPQVbih LRl[N i inHozWHp puB qu Oh vx   ohx  UH",
# "Uo`I k OWcvC i [w R drz `YLkv  TcaaWIoQ J Dbf   aUmV`b vgEyypVz  Sqc EHNhVSF ac er VzmOF U  k"
#  "U p]NwdmbcycNOLmpHA   ntK qvW xSJ u ^arNaJ",
#  "y_  G jxPvFRZ I hUM[hYgrxyQB  bbFI`hXdyD ZywEpBpV]dxdL z EbvbXrfP YIFe fuEamg K_nk   e qn[a  [GAF  Mv yY",
#  "s^wo  FlN`vk NN[BIC  DLJPQ pG[ TM`HUOfIkPGVn vD[ Hf I k YVm CW]Sa Zkr  B E^ uk p[O^]vQW",
#  "B^_pAhIi  ZcG[Y i   airswaSy   y[ozGvQHLJ h[amMHB  a rkciMVNS S[OC",
 #"YHbKn_ Q ]zY[]ZFBrdVx tq  IvfMx_PY esHDHQr  b Kq^e Fzsm qXX wWheecW [``cZxSMgBwaWW",
#  " U kbadyuRusj Yw  UonHQuRf Zk sXKyK[J JEIg ekO PE aRyOyMJ a_pt   U J d",
#  " Qns[gGUM Ieg P^q K u  CqDkXSSF `He iQf Emi v"
# "Xz Uv  WMKA G`Jg  jpgJLmuQgFTgIp[czTgPXtoP_Qj x ZpiqlgwuYR sKUeBq UV_YizVcePn kJD sKt  C N qK",
#   "JwFwC sKQHGTLWrBcx^   q t E [VdlX UsCyls_  YzbwBvi  UYR^GWE   [^k A uP[qeL  RFR LAcj]bBgs  iG   K ",
#  "FQo]FsGuY  y mPt QgKDcmqiQxH`_T xIaJmky E`PjMj^hGcFAHxId pMkW KfDdFA  S "
#  "WPJ ay p BnrjTpbHL` qBSKx wz wkYjBa`dJq ",
#    "Wh_O  OcYNuB w pNIu^wKfcUJWTL L[UGfEX gYan  HBoG"
