"""One-off: write ib_accounts.json from the folders that already hold your keys."""
import json, pathlib
ACCOUNTS = {
 "USA.PHE":  ("PHEAPIKEY", "ab441e7e1e737e640753", "EPQXjH33ez1PkBK3seO/+iIrgaCD7x2tFViI87iIUM1n85fRWkMYEFb5cKSjKsH1K89U0pxbOJKjzbp4DQbtJl37/yDNb0q5KieEwpzxhax5gA0Ae0+1CM5E9IFE0O/li32sswVDG28J0nwqn5p6VwHp9KiJdtGV0QmXzC36KCneRccaaHqEQGQT2fu723uBuWq7Jz0bhLBGhporsgxIkJVcrglck9WaH3fO62iGIk95LrSUcKKgc79P6iSJQDJvnEwXOkOZLr9Ol8WdoKZoaCHoQTgP1Vsc3cecq8vA02IZgz8N2DuMhoo9EPsEXRQCXOsTOpleHFviHpL6qAwTAw==", "~/ibkr-phe"),
 "USA.PHC":  ("PHCAPIKEY", "faef333798c03d6d26d2", "s+jp9ISYHJS5uost/7NnWfymu2hEapB6lE+MSyRpB0YH7dJIJUOU0Odi7z9NCQjrwui8q69Qg0ZTyBZEfihPE7Jl8Qel8vIu0MxH2e/Jv/KlEIHv+JbZ38RDda6tg2/hgRvTRYJw9mU79KZLP6gFJJWeBYrbOYfIBXHrF8j3hDdNaei48eGpuP889agTVM8jbu6l96W3mKoscVApOnFMhtt8FMIbCjl6R205k4tXE9LsVJKgP+2aStXVE+RF1lMioS/iZetO0Rzr95hPp4OJJyqJ+uQQA4HjAuqnRGmruqTFJPJM0pkvaE2lPf2O76WOoTic5WnUSCQtYf8Rb9Qeog==", "~/ibkr-phc"),
 "USA.PHIC":  ("PHFAPIKEY", "18155579cf0d8bc5ac6f", "FOken/Bzs1H7zi/HSRV79v8gL31ipMVpXL1PZMU8yFWQn8/+x0zNvcMteF6Ug93pOohg0T09RGPZRPGjh5mkaPBcVD33QvnnzE3X2WjZI7UE3AqfsUWp8n4ax5S9RRz1NqXLIalZ5GsXf3TDmyjGwuSqiaQfTMVd2uHpJTCkUyuYznMPEJGMMEhb+NyKjHOb6rAeYudJWrsF6l6AhC3EvmmOVtrJye4n2Pv9C8wfpkeKcWLwOjkHjJXik3DOQaCBXoDnIMhguS8NoMEX5AJSvDnnkjLr742mKhPp5HKSgDHyAKlqHLB9Nhjigqforof90wVVHL/MYUd5FZt1MxrA3g==", "~/ibkr-pcf"),
 "USA.ACADEMY": ("PEACAPIKY", "05d605eb9b057c98e2a7", "rL4bHDaNeJO0Krvs8abwX/SUAPKSFtT7NHqGBCq9tYR0z5D7Dt6acDrPTL4cfbW29P5zcj5ctd58Be7MXsRLfHffNh8xcWaf9vWCz3Z2gsi4KGLbYOsCr/ZsG5fYs5eJAycf/v+7LCxwgS8NJAlMzjVZ0d4xYg7/45jpPaML4protRIpd2rhsADLtyRQ40ajkZeHvsJ7Bn47Qwks5nfNdk/wDoLdfRl5wDLyuBSyNuCD8NQvA0/MxrRtL1jRvBC250fir/AwPWqSOeCG589av87HWYyxrLseD0EpeBVEKebet4xWuJzyBnfFFzAiPkyamHCDW4/g+F2ryWJ+m5EXSQ==", "~/ibkr-peace"),
 "USA.AEROSPACE": ("AEROAPIKY", "03001d45266108553694", "JGsHUpiCdwk+39a3fvB6nfjZ6RJ9g8unispE84KxZ/blvWgUVugSkaFPcOBeFDcUcHfQTeicng7sm14fAsJTo8fvx/VnD3mx3s4RPHVs31YIT32kZk9zEIsT6XiQPZzidBZN8pbdaB/uzffMS00VOP5YWp+5y/jjUqLwgkCJDdDujGHfvUEuKRdaV0mNeUbSBNnptVAPuuOdz8GfB1O3FQY7CbPjIcT8q/1h8WTiseHj8BhQQNYNxkrrcaPIaC/W6f9hQ7pGb/w5WyLPIocNB4m9UcZsAU//6IAe/qt6YIF6GKrNf5XK+CJgVO/okHsTCFcuTxksBJusSJjmWOZC+A==", "~/ibkr-aero"),
}
cfg = {n: {"consumer_key": ck, "access_token": tok, "access_token_secret": sec, "folder": f}
       for n, (ck, tok, sec, f) in ACCOUNTS.items()}
p = pathlib.Path(__file__).with_name('ib_accounts.json')
p.write_text(json.dumps(cfg, indent=2))
try:
    p.chmod(0o600)
except Exception:
    pass
print("wrote", p, "with:", ", ".join(cfg))
for n, a in cfg.items():
    folder = pathlib.Path(a['folder']).expanduser()
    missing = [f for f in ('private_signature.pem','private_encryption.pem','dhparam.pem') if not (folder/f).exists()]
    print(f"  {n:<6} {folder}  {'OK' if not missing else 'MISSING: ' + ', '.join(missing)}")
