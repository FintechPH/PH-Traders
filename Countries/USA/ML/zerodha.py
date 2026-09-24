"""zerodha.py - Zerodha (Kite Connect) from the command line.

    python zerodha.py login                       once a day: prints a URL, you paste back the request_token
    python zerodha.py holdings                    cash, holdings and P&L
    python zerodha.py positions                   today's positions
    python zerodha.py orders                      working orders
    python zerodha.py quote INFY                  last price on NSE and BSE (paid plan only)
    python zerodha.py quote INFY --exchange BSE
    python zerodha.py buy INFY 10 --limit 1450 --exchange BSE
    python zerodha.py buy INFY 10 --limit 1450
    python zerodha.py buy INFY 10 --market
    python zerodha.py sell INFY 10 --limit 1500
    python zerodha.py cancel 250101000000123

Credentials live in zerodha_config.json beside this file:
    {"api_key": "...", "api_secret": "...", "default_exchange": "NSE", "default_product": "CNC"}

The access token is saved in zerodha_token.json and expires each morning, so `login`
is the first command of the day.
"""
import hashlib
import json
import pathlib
import sys
from datetime import date

import requests

HERE = pathlib.Path(__file__).parent
CONFIG = HERE / 'zerodha_config.json'
TOKEN = HERE / 'zerodha_token.json'
BASE = 'https://api.kite.trade'
LOGIN_URL = 'https://kite.zerodha.com/connect/login?v=3&api_key={api_key}'

OPEN_STATES = ('OPEN', 'TRIGGER PENDING', 'AMO REQ RECEIVED', 'PUT ORDER REQ RECEIVED', 'VALIDATION PENDING')


def load_config():
    if not CONFIG.exists():
        sys.exit(f"Missing {CONFIG}. Create it with your api_key and api_secret - see the header of this file.")
    cfg = json.loads(CONFIG.read_text())
    for key in ('api_key', 'api_secret'):
        if not cfg.get(key) or str(cfg[key]).startswith('your-'):
            sys.exit(f"{CONFIG}: {key} is not filled in yet.")
    cfg.setdefault('default_exchange', 'NSE')
    cfg.setdefault('default_product', 'CNC')
    return cfg


def load_token():
    if not TOKEN.exists():
        return None
    saved = json.loads(TOKEN.read_text())
    if saved.get('date') != date.today().isoformat():
        return None                      # Kite tokens expire each morning
    return saved.get('access_token')


def save_token(token):
    TOKEN.write_text(json.dumps({'date': date.today().isoformat(), 'access_token': token}, indent=2))
    try:
        TOKEN.chmod(0o600)
    except Exception:
        pass


class Kite:
    def __init__(self, cfg, access_token=None):
        self.cfg, self.token = cfg, access_token

    def _headers(self):
        h = {'X-Kite-Version': '3'}
        if self.token:
            h['Authorization'] = f"token {self.cfg['api_key']}:{self.token}"
        return h

    def _call(self, method, path, **kw):
        r = requests.request(method, f"{BASE}{path}", headers=self._headers(), timeout=30, **kw)
        try:
            body = r.json()
        except ValueError:
            sys.exit(f"Unexpected reply from Zerodha ({r.status_code}): {r.text[:200]}")
        if body.get('status') == 'error' or r.status_code >= 400:
            message = body.get('message', str(body)[:200])
            if body.get('error_type') == 'TokenException':
                message += "\n  The access token has expired - run: python zerodha.py login"
            sys.exit(f"Zerodha error: {message}")
        return body.get('data')

    # ---- session ----
    def exchange_request_token(self, request_token):
        raw = self.cfg['api_key'] + request_token + self.cfg['api_secret']
        checksum = hashlib.sha256(raw.encode()).hexdigest()
        data = self._call('POST', '/session/token',
                          data={'api_key': self.cfg['api_key'], 'request_token': request_token,
                                'checksum': checksum})
        return data['access_token'], data.get('user_name', ''), data.get('user_id', '')

    # ---- reads ----
    def margins(self):
        return self._call('GET', '/user/margins') or {}

    def holdings(self):
        return self._call('GET', '/portfolio/holdings') or []

    def positions(self):
        return (self._call('GET', '/portfolio/positions') or {}).get('net') or []

    def orders(self):
        return self._call('GET', '/orders') or []

    def ltp(self, instruments):
        """instruments: 'NSE:INFY' or ['NSE:INFY', 'BSE:INFY'] - Kite repeats the i parameter."""
        if isinstance(instruments, str):
            instruments = [instruments]
        return self._call('GET', '/quote/ltp', params=[('i', i) for i in instruments]) or {}

    # ---- orders ----
    def place(self, exchange, symbol, side, qty, order_type, price=None, product='CNC',
              validity='DAY', market_protection=5):
        payload = {'tradingsymbol': symbol, 'exchange': exchange, 'transaction_type': side,
                   'order_type': order_type, 'quantity': str(qty), 'product': product,
                   'validity': validity}
        if order_type == 'LIMIT':
            payload['price'] = f"{price:.2f}"
        else:
            payload['market_protection'] = str(market_protection)   # 0 is rejected as unprotected
        return self._call('POST', '/orders/regular', data=payload)

    def cancel(self, order_id):
        return self._call('DELETE', f'/orders/regular/{order_id}')


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ---- commands ----

def cmd_login(k, args):
    print("1. Open this in a browser and log in to Zerodha:\n")
    print("   " + LOGIN_URL.format(api_key=k.cfg['api_key']) + "\n")
    print("2. After logging in you land on your redirect URL. Copy the request_token from it:")
    print("   http://127.0.0.1:8000/?request_token=XXXXXXXX&action=login&status=success\n")
    request_token = (args.request_token or input("3. Paste the request_token here: ")).strip()
    if not request_token:
        sys.exit("No request_token given.")
    token, name, user = k.exchange_request_token(request_token)
    save_token(token)
    print(f"\nLogged in as {name} ({user}). Token saved, valid until tomorrow morning.")


def cmd_holdings(k, args):
    m = k.margins() or {}
    eq = (m.get('equity') or {}).get('available') or {}
    print(f"Cash available {num(eq.get('live_balance') or eq.get('cash')):>14,.2f}")
    rows = k.holdings()
    if not rows:
        print("No holdings.")
        return
    w = max([8] + [len(str(r.get('tradingsymbol', ''))) + 1 for r in rows])
    print(f"\n  {'Symbol':<{w}}{'Exch':<6}{'Qty':>7}{'Avg cost':>11}{'Last':>10}{'Value':>13}{'P&L':>12}{'%':>8}")
    tot_cost = tot_val = 0.0
    for r in rows:
        qty = num(r.get('quantity')) + num(r.get('t1_quantity'))
        avg, last = num(r.get('average_price')), num(r.get('last_price'))
        cost, val = avg * qty, last * qty
        pnl = num(r.get('pnl'), val - cost)
        tot_cost += cost
        tot_val += val
        pct = (pnl / cost * 100) if cost else 0.0
        print(f"  {r.get('tradingsymbol',''):<{w}}{str(r.get('exchange','')):<6}{qty:>7.0f}{avg:>11.2f}{last:>10.2f}"
              f"{val:>13,.2f}{pnl:>+12,.2f}{pct:>+7.1f}%")
    pnl = tot_val - tot_cost
    pct = (pnl / tot_cost * 100) if tot_cost else 0.0
    print(f"  {'TOTAL':<{w}}{'':<6}{'':>7}{'':>11}{'':>10}{tot_val:>13,.2f}{pnl:>+12,.2f}{pct:>+7.1f}%")


def cmd_positions(k, args):
    rows = [p for p in k.positions() if num(p.get('quantity'))]
    if not rows:
        print("No open positions today.")
        return
    print(f"  {'Symbol':<14}{'Exch':<6}{'Qty':>7}{'Avg':>10}{'Last':>10}{'P&L':>12}  Product")
    for p in rows:
        print(f"  {p.get('tradingsymbol',''):<14}{str(p.get('exchange','')):<6}{num(p.get('quantity')):>7.0f}"
              f"{num(p.get('average_price')):>10.2f}{num(p.get('last_price')):>10.2f}"
              f"{num(p.get('pnl')):>+12,.2f}  {p.get('product','')}")


def cmd_orders(k, args):
    rows = [o for o in k.orders() if str(o.get('status', '')).upper() in OPEN_STATES]
    if not rows:
        print("No open orders.")
        return
    for o in rows:
        print(f"{o.get('order_id',''):<22} {str(o.get('exchange','')):<4} {o.get('tradingsymbol',''):<14} "
              f"{o.get('transaction_type',''):<4} "
              f"{num(o.get('filled_quantity')):.0f}/{num(o.get('quantity')):.0f}  "
              f"{o.get('order_type','')} {o.get('price','')}  {o.get('product','')}  {o.get('status','')}")


def cmd_quote(k, args):
    exchanges = ['NSE', 'BSE'] if args.exchange == 'BOTH' else [args.exchange]
    keys = [f"{e}:{args.symbol}" for e in exchanges]
    data = k.ltp(keys)
    shown = False
    for key in keys:
        row = data.get(key)
        if row:
            shown = True
            print(f"  {key:<14} last {num(row.get('last_price')):>12,.2f}")
        else:
            print(f"  {key:<14} not listed / no data")
    if not shown:
        sys.exit("No quotes returned. Live data needs the paid Kite Connect plan "
                 "(the free Personal plan covers orders and holdings only).")


def held_qty(k, symbol, exchange=None):
    def match(row):
        if str(row.get('tradingsymbol', '')).upper() != symbol:
            return False
        got = str(row.get('exchange', '')).upper()
        return exchange is None or not got or got == exchange   # blank exchange counts, don't under-report
    total = sum(num(h.get('quantity')) + num(h.get('t1_quantity')) for h in k.holdings() if match(h))
    total += sum(num(p.get('quantity')) for p in k.positions() if match(p))
    return total


def committed_sells(k, symbol, exchange=None):
    return sum(num(o.get('quantity')) - num(o.get('filled_quantity'))
               for o in k.orders()
               if str(o.get('tradingsymbol', '')).upper() == symbol
               and (exchange is None or not str(o.get('exchange', '')).upper()
                    or str(o.get('exchange', '')).upper() == exchange)
               and str(o.get('transaction_type', '')).upper() == 'SELL'
               and str(o.get('status', '')).upper() in OPEN_STATES)


def cmd_trade(k, args, side):
    symbol, qty = args.symbol, args.quantity
    price = None if args.market else args.limit
    kind = 'market' if price is None else f"limit {price:.2f}"
    exchange, product = args.exchange, args.product

    print(f"{side} {qty} {exchange}:{symbol} at {kind}, {product}, {args.validity}")
    if side == 'SELL':
        held = held_qty(k, symbol, exchange)
        committed = committed_sells(k, symbol, exchange)
        print(f"  holding {held:g} on {exchange}, {committed:g} already committed to open sells")
        if qty > held - committed:
            sys.exit(f"Refusing: only {held - committed:g} free to sell.")
    elif price is not None:
        print(f"  estimated cost {price * qty:,.2f}")

    if input("Type yes to send: ").strip().lower() != 'yes':
        sys.exit("Not sent.")
    data = k.place(exchange, symbol, side, qty, 'MARKET' if price is None else 'LIMIT',
                   price, product, args.validity)
    print("RESULT: order", (data or {}).get('order_id', data))


def cmd_cancel(k, args):
    if input(f"Cancel order {args.order_id}? Type yes: ").strip().lower() != 'yes':
        sys.exit("Not cancelled.")
    data = k.cancel(args.order_id)
    print("RESULT: order", (data or {}).get('order_id', data))


def build_parser():
    import argparse
    p = argparse.ArgumentParser(prog='zerodha.py')
    sub = p.add_subparsers(dest='command', required=True)

    q = sub.add_parser('login', help='daily login (token expires each morning)')
    q.add_argument('request_token', nargs='?', help='paste it here, or leave blank to be prompted')

    for cmd in ('holdings', 'positions', 'orders'):
        sub.add_parser(cmd)

    q = sub.add_parser('quote', help='last price on NSE, BSE or both')
    q.add_argument('symbol', type=str.upper)
    q.add_argument('--exchange', default='BOTH', type=str.upper,
                   choices=('NSE', 'BSE', 'BOTH'), help='default BOTH')

    for cmd in ('buy', 'sell'):
        q = sub.add_parser(cmd)
        q.add_argument('symbol', type=str.upper)
        q.add_argument('quantity', type=int)
        g = q.add_mutually_exclusive_group(required=True)
        g.add_argument('--limit', type=float)
        g.add_argument('--market', action='store_true')
        q.add_argument('--exchange', default='NSE', type=str.upper,
                       choices=('NSE', 'BSE'), help='NSE (default) or BSE')
        q.add_argument('--product', default='CNC', type=str.upper,
                       choices=('CNC', 'MIS', 'NRML'), help='CNC delivery, MIS intraday')
        q.add_argument('--validity', default='DAY', type=str.upper, choices=('DAY', 'IOC'))

    q = sub.add_parser('cancel'); q.add_argument('order_id')
    return p


def main(argv=None):
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    cfg = load_config()
    if args.command in ('buy', 'sell'):
        if args.quantity <= 0:
            sys.exit("Quantity must be positive.")
        if not args.market and args.limit <= 0:
            sys.exit("Limit price must be positive.")

    if args.command == 'login':
        return cmd_login(Kite(cfg), args) or 0

    token = load_token()
    if not token:
        sys.exit("No valid access token for today. Run: python zerodha.py login")
    k = Kite(cfg, token)
    handlers = {'holdings': cmd_holdings, 'positions': cmd_positions, 'orders': cmd_orders,
                'quote': cmd_quote, 'cancel': cmd_cancel}
    if args.command in ('buy', 'sell'):
        cmd_trade(k, args, args.command.upper())
    else:
        handlers[args.command](k, args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
