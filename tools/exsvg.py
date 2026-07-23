import json, math, html

def _norm(c):
    if not c or c=='transparent': return None
    if isinstance(c,str) and c.startswith('url('): return None
    if isinstance(c,str) and len(c)==9:      # #RRGGBBAA
        if c[7:9].lower()=='00': return None
        return c[:7]
    return c

def _bbox(els):
    xs=[];ys=[]
    for e in els:
        x=e.get('x',0);y=e.get('y',0);w=e.get('width',0)or 0;h=e.get('height',0)or 0
        xs+=[x,x+w];ys+=[y,y+h]
        for _p in (e.get('points') or []):
            xs.append(x+_p[0]);ys.append(y+_p[1])
    return (min(xs),min(ys),max(xs),max(ys)) if xs else (0,0,1,1)

def _rot(e):
    a=e.get('angle',0) or 0
    if not a: return ''
    cx=e.get('x',0)+(e.get('width',0)or 0)/2; cy=e.get('y',0)+(e.get('height',0)or 0)/2
    return f' transform="rotate({a*180/math.pi:.2f} {cx:.2f} {cy:.2f})"'

def _fillfor(e):
    """Return fill value respecting fillStyle. hachure/cross-hatch -> none (never obscure)."""
    bg=_norm(e.get('backgroundColor'))
    if not bg: return 'none'
    fs=e.get('fillStyle','hachure')
    return bg if fs=='solid' else 'none'

def _el(e):
    t=e.get('type'); x=e.get('x',0);y=e.get('y',0);w=e.get('width',0)or 0;h=e.get('height',0)or 0
    sw=e.get('strokeWidth',1)or 1; op=(e.get('opacity',100))/100.0
    st=_norm(e.get('strokeColor')) or 'none'
    fl=_fillfor(e); r=_rot(e)
    common=f'stroke="{st}" stroke-width="{sw}" opacity="{op}" fill="{fl}"'
    if t=='rectangle':
        rad=8 if e.get('roundness') else 0
        return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rad}" {common}{r}/>'
    if t=='ellipse':
        return f'<ellipse cx="{x+w/2:.2f}" cy="{y+h/2:.2f}" rx="{w/2:.2f}" ry="{h/2:.2f}" {common}{r}/>'
    if t=='diamond':
        pts=f"{x+w/2:.2f},{y:.2f} {x+w:.2f},{y+h/2:.2f} {x+w/2:.2f},{y+h:.2f} {x:.2f},{y+h/2:.2f}"
        return f'<polygon points="{pts}" {common}{r}/>'
    if t in('line','draw','freedraw'):
        pts=e.get('points') or [[0,0],[w,h]]
        d=" ".join(f"{x+_p[0]:.2f},{y+_p[1]:.2f}" for _p in pts)
        # filled shape when it has a solid background; else just a stroked path
        return f'<polyline points="{d}" fill="{fl}" stroke="{st}" stroke-width="{sw}" opacity="{op}" stroke-linecap="round" stroke-linejoin="round"{r}/>'
    if t=='arrow':
        pts=e.get('points') or [[0,0],[w,h]]
        d=" ".join(f"{x+_p[0]:.2f},{y+_p[1]:.2f}" for _p in pts)
        return f'<polyline points="{d}" fill="none" stroke="{st}" stroke-width="{sw}" opacity="{op}" stroke-linecap="round" stroke-linejoin="round"{r}/>'
    if t=='text':
        fs=e.get('fontSize',16); txt=html.escape(e.get('text','') or '')
        col=_norm(e.get('strokeColor')) or '#1e1e1e'
        return f'<text x="{x:.2f}" y="{y+fs:.2f}" font-size="{fs}" fill="{col}" opacity="{op}" font-family="sans-serif"{r}>{txt}</text>'
    return ''

def render(elements, pad=6):
    x0,y0,x1,y1=_bbox(elements)
    w=max(1,x1-x0+2*pad); h=max(1,y1-y0+2*pad)
    body="".join(_el(e) for e in elements)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-pad:.2f} {y0-pad:.2f} {w:.2f} {h:.2f}" '
            f'width="{w:.0f}" height="{h:.0f}">{body}</svg>')
