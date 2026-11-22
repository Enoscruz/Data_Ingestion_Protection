"""Gera os desenhos da arquitetura: estrutura.svg e vida-do-dado.svg."""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(RAIZ, "arquitetura")


def _caixa(x, y, w, h, titulo, sub="", cor="#EFEDF2", borda="#DFDBE5"):
    t = '<text x="%d" y="%d" text-anchor="middle" font-family="Segoe UI,Arial" font-size="13" font-weight="600" fill="#1D1A22">%s</text>' % (
        x + w // 2, y + (h // 2 if not sub else h // 2 - 6), titulo)
    s = ""
    if sub:
        s = '<text x="%d" y="%d" text-anchor="middle" font-family="Consolas,monospace" font-size="10" fill="#726B7C">%s</text>' % (
            x + w // 2, y + h // 2 + 12, sub)
    return ('<g><rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="%s" stroke-width="1.5"/>%s%s</g>'
            % (x, y, w, h, cor, borda, t, s))


def _seta(x1, y1, x2, y2, rotulo=""):
    g = ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#0B6BCB" stroke-width="2" marker-end="url(#ponta)"/>'
         % (x1, y1, x2, y2))
    if rotulo:
        g += ('<text x="%d" y="%d" text-anchor="middle" font-family="Consolas,monospace" font-size="9" fill="#726B7C">%s</text>'
              % ((x1 + x2) // 2, (y1 + y2) // 2 - 4, rotulo))
    return g


DEFS = ('<defs><marker id="ponta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="#0B6BCB"/></marker></defs>')


def estrutura():
    p = [DEFS]
    p.append('<text x="20" y="30" font-family="Barlow Condensed,Arial" font-size="20" font-weight="700" fill="#F0265D">Estrutura da plataforma</text>')
    p.append(_caixa(20, 90, 130, 54, "Origem", "banco + cliques", "#FDF2F6", "#F0265D"))
    p.append(_seta(150, 117, 200, 117, "carga"))
    p.append(_caixa(200, 90, 140, 54, "Bronze", "cópia fiel", "#EFEDF2"))
    p.append(_seta(340, 117, 390, 117, "contrato"))
    p.append(_caixa(390, 90, 140, 54, "Silver", "validada · pseudônimo", "#E8F1FC", "#0B6BCB"))
    p.append(_seta(530, 117, 580, 117, "agrega"))
    p.append(_caixa(580, 90, 130, 54, "Gold", "consumo · K", "#E7F5EC", "#0A7D3F"))
    p.append(_seta(410, 144, 430, 180, "desvio"))
    p.append(_caixa(390, 180, 150, 46, "Quarentena", "linha + motivo", "#FBF1DF", "#B45309"))
    p.append(_caixa(20, 200, 150, 46, "Log · mudanças", "CDC · offset", "#E7F5EC", "#0A7D3F"))
    p.append(_seta(170, 223, 200, 150, "em ordem"))
    p.append(_caixa(20, 280, 150, 46, "Tópico navegação", "N leitores", "#E7F5EC", "#0A7D3F"))
    p.append(_seta(170, 303, 250, 300, "offsets"))
    p.append(_caixa(20, 360, 150, 46, "acordo + catálogo", "governança", "#EFEDF2"))
    p.append(_caixa(390, 250, 150, 46, "chave", "fora do código", "#FDECEC", "#C1121F"))
    p.append(_caixa(580, 250, 130, 46, "cópias", "3-2-1-1-0", "#EFEDF2"))
    p.append(_caixa(390, 320, 320, 46, "lista de eliminação", "esquecer · evidência", "#EFEDF2"))
    return _svg(730, 400, p)


def vida_do_dado():
    p = [DEFS]
    p.append('<text x="20" y="30" font-family="Barlow Condensed,Arial" font-size="20" font-weight="700" fill="#F0265D">A vida de um dado pessoal</text>')
    etapas = [
        ("cadastro", "CPF real", "#FDF2F6", "#F0265D"),
        ("log", "mudança real · 24 h", "#E7F5EC", "#0A7D3F"),
        ("bronze", "CPF real", "#EFEDF2", "#DFDBE5"),
        ("silver", "pseudônimo", "#E8F1FC", "#0B6BCB"),
        ("gold", "agregado", "#E7F5EC", "#0A7D3F"),
        ("eliminação", "ausente", "#FDECEC", "#C1121F"),
    ]
    x = 20
    for i, (t, s, cor, borda) in enumerate(etapas):
        p.append(_caixa(x, 90, 130, 56, t, s, cor, borda))
        if i < len(etapas) - 1:
            p.append(_seta(x + 130, 118, x + 165, 118))
        x += 170
    p.append('<text x="20" y="190" font-family="Segoe UI,Arial" font-size="12" fill="#726B7C">O CPF real vive só na origem e na bronze; na silver vira pseudônimo; o esquecimento mata o vínculo.</text>')
    return _svg(1090, 230, p)


def _svg(largura, altura, partes):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">'
            '<rect width="%d" height="%d" fill="#FFFFFF"/>%s</svg>'
            % (largura, altura, largura, altura, largura, altura, "".join(partes)))


def gerar():
    os.makedirs(DEST, exist_ok=True)
    for nome, conteudo in (("estrutura.svg", estrutura()), ("vida-do-dado.svg", vida_do_dado())):
        with open(os.path.join(DEST, nome), "w", encoding="utf-8") as f:
            f.write(conteudo)
    return DEST


if __name__ == "__main__":
    print("desenhos em", gerar())
